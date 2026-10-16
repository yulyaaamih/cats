import io
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio

import asyncpg
import httpx
from PIL import Image

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, Response, JSONResponse

import settings

logger = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS cats (
    id SERIAL PRIMARY KEY,
    img_url TEXT NOT NULL
)
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=5)
    async with app.state.db.acquire() as conn:
        await conn.execute(CREATE_TABLE)
    yield
    await app.state.db.close()


app = FastAPI(lifespan=lifespan)

INDEX_HTML = Path(__file__).parent / "static" / "index.html"

CAT_API = "https://api.thecatapi.com/v1/images/search"
FALLBACK = "https://cataas.com/cat"


MAX_SIDE = 400
QUALITY = 80


@app.get("/cat.jpg")
async def cat_image():
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            meta = await client.get(CAT_API)
            meta.raise_for_status()
            img_url = meta.json()[0]["url"]
            img = await client.get(img_url)
            img.raise_for_status()

        try:
            await app.state.db.execute("INSERT INTO cats (img_url) VALUES ($1)", img_url)
        except Exception:
            logger.exception("failed to save img_url")

        im = Image.open(io.BytesIO(img.content)).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=QUALITY, optimize=True)
        return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception:
        return Response(status_code=302, headers={"Location": FALLBACK})


@app.get("/cats")
async def list_cats(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    rows = await app.state.db.fetch(
        "SELECT img_url FROM cats ORDER BY id DESC LIMIT $1 OFFSET $2", limit, offset
    )
    return [row["img_url"] for row in rows]


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(INDEX_HTML)


@app.get("/health")
async def health():

    try:
        await asyncio.wait_for(app.state.db.fetchval("SELECT 1"), timeout=2)
    except Exception as e:
        logger.warning("db ping failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "unavailable"},
        )

    return {"status": "ok"}