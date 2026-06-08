import io

import httpx
from PIL import Image

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)

CAT_API = "https://api.thecatapi.com/v1/images/search"
FALLBACK = "https://cataas.com/cat"


MAX_SIDE = 400   # макс. сторона картинки в пикселях
QUALITY = 80     # качество jpeg


@app.get("/cat.jpg")
async def cat_image():
    """Сервер качает котика, ужимает и отдаёт лёгкий jpeg."""
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
    return HTML


HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Котики</title>
<style>
  body{
    font-family: system-ui, sans-serif;
    min-height:100vh;
    margin:0;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:20px;
    background:#fafafa;
  }
  h1{font-weight:600;color:#333}
  img{
    max-width:400px;
    width:90vw;
    border-radius:12px;
    box-shadow:0 4px 16px rgba(0,0,0,.12);
  }
  button{
    font-size:16px;
    padding:10px 24px;
    border:none;
    border-radius:8px;
    background:#333;
    color:#fff;
    cursor:pointer;
  }
  button:hover{background:#555}
  button:disabled{opacity:.5;cursor:wait}
</style>
</head>
<body>
  <h1>🐱 Котик</h1>
  <img id="cat" src="/cat.jpg" alt="кот">
  <button id="more">Ещё</button>
<script>
  const img = document.getElementById('cat');
  const btn = document.getElementById('more');
  btn.addEventListener('click', () => {
    btn.disabled = true;
    img.src = '/cat.jpg?' + Date.now();   // ?время — чтобы браузер не брал из кеша
  });
  img.addEventListener('load', () => btn.disabled = false);
  img.addEventListener('error', () => btn.disabled = false);
</script>
</body>
</html>"""