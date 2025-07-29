import socket
import threading
import cv2
import numpy as np
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Camera Stream Server", version="1.0.0")

# Configurar CORS para Azure
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_frame = None

def udp_receiver():
    global latest_frame
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Usar porta configurável para Azure
    port = int(os.environ.get("UDP_PORT", 5000))
    sock.bind(("0.0.0.0", port))
    print(f"UDP receiver listening on port {port}")

    while True:
        try:
            data, _ = sock.recvfrom(65536)  # tamanho máximo de pacote UDP
            np_arr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                latest_frame = frame
        except Exception as e:
            print(f"Error receiving UDP data: {e}")
            continue

def mjpeg_stream():
    while True:
        if latest_frame is not None:
            _, buffer = cv2.imencode('.jpg', latest_frame)
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

@app.get("/")
def root():
    return {"message": "Camera Stream Server is running", "endpoints": ["/camera", "/health"]}

@app.get("/health")
def health_check():
    return {"status": "healthy", "frame_available": latest_frame is not None}

@app.get("/camera")
def camera():
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

threading.Thread(target=udp_receiver, daemon=True).start()
