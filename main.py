import io
from pathlib import Path

import httpx
from PIL import Image

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

INDEX_HTML = Path(__file__).parent / "static" / "index.html"

Instrumentator().instrument(app).expose(app)

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

        im = Image.open(io.BytesIO(img.content)).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))   # ресайз с сохранением пропорций
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=QUALITY, optimize=True)
        return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception:
        return Response(status_code=302, headers={"Location": FALLBACK})


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(INDEX_HTML)