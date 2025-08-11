import socket
import threading
import cv2
import numpy as np
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
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
    port = int(os.environ.get("UDP_PORT", 5001))
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
    return {
        "message": "Camera Stream Server is running", 
        "endpoints": {
            "/camera": "Stream da câmera UDP",
            "/mobile": "Interface para câmera móvel",
            "/health": "Status do servidor",
            "/docs": "Documentação da API"
        },
        "instructions": {
            "mobile": "Acesse /mobile no seu celular para usar a câmera frontal",
            "desktop": "Use /camera para ver o stream da câmera conectada via UDP"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "frame_available": latest_frame is not None}

@app.get("/mobile", response_class=HTMLResponse)
def mobile_camera():
    """Página web para capturar câmera frontal do mobile"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Câmera Móvel</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                background-color: #000;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
            }
            .container {
                max-width: 100%;
                margin: 0 auto;
            }
            h1 {
                color: #00ff88;
                margin-bottom: 20px;
            }
            #videoContainer {
                position: relative;
                margin: 20px auto;
                max-width: 100%;
                border: 2px solid #00ff88;
                border-radius: 10px;
                overflow: hidden;
            }
            video {
                width: 100%;
                height: auto;
                max-height: 70vh;
                object-fit: cover;
            }
            .controls {
                margin: 20px 0;
            }
            button {
                background-color: #00ff88;
                color: black;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 25px;
                margin: 10px;
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s;
            }
            button:hover {
                background-color: #00cc6a;
                transform: scale(1.05);
            }
            button:disabled {
                background-color: #666;
                color: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            .status.success {
                background-color: rgba(0, 255, 136, 0.2);
                border: 1px solid #00ff88;
            }
            .status.error {
                background-color: rgba(255, 0, 0, 0.2);
                border: 1px solid #ff0000;
            }
            .status.info {
                background-color: rgba(0, 136, 255, 0.2);
                border: 1px solid #0088ff;
            }
            .switch-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                background-color: rgba(0, 255, 136, 0.8);
                z-index: 10;
                padding: 10px;
                border-radius: 50%;
                width: 50px;
                height: 50px;
            }
            .info {
                background-color: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 Câmera Móvel</h1>
            
            <div class="info">
                <h3>ℹ️ Como usar:</h3>
                <ul>
                    <li>Clique em "Iniciar Câmera" para ativar</li>
                    <li>Permita o acesso à câmera quando solicitado</li>
                    <li>Use o botão de alternância para trocar entre câmeras</li>
                    <li>A imagem será exibida em tempo real</li>
                </ul>
            </div>

            <div id="videoContainer">
                <video id="video" autoplay muted playsinline></video>
                <button id="switchCamera" class="switch-btn" title="Alternar câmera" style="display: none;">🔄</button>
            </div>

            <div class="controls">
                <button id="startBtn">Iniciar Câmera</button>
                <button id="stopBtn" disabled>Parar Câmera</button>
            </div>

            <div id="status" class="status info">
                Clique em "Iniciar Câmera" para começar
            </div>
        </div>

        <script>
            const video = document.getElementById('video');
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const switchBtn = document.getElementById('switchCamera');
            const status = document.getElementById('status');

            let currentStream = null;
            let currentFacingMode = 'user'; // 'user' = frontal, 'environment' = traseira

            function updateStatus(message, type = 'info') {
                status.textContent = message;
                status.className = `status ${type}`;
            }

            async function startCamera() {
                try {
                    updateStatus('Iniciando câmera...', 'info');
                    
                    const constraints = {
                        video: {
                            facingMode: currentFacingMode,
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        },
                        audio: false
                    };

                    currentStream = await navigator.mediaDevices.getUserMedia(constraints);
                    video.srcObject = currentStream;

                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                    switchBtn.style.display = 'block';

                    updateStatus(`✅ Câmera ativa (${currentFacingMode === 'user' ? 'Frontal' : 'Traseira'})`, 'success');

                } catch (error) {
                    console.error('Erro ao acessar câmera:', error);
                    
                    let errorMessage = 'Erro ao acessar câmera: ';
                    if (error.name === 'NotAllowedError') {
                        errorMessage += 'Permissão negada. Permita o acesso à câmera nas configurações do navegador.';
                    } else if (error.name === 'NotFoundError') {
                        errorMessage += 'Nenhuma câmera encontrada.';
                    } else if (error.name === 'NotSupportedError') {
                        errorMessage += 'Navegador não suporta acesso à câmera.';
                    } else {
                        errorMessage += error.message;
                    }
                    
                    updateStatus(errorMessage, 'error');
                }
            }

            function stopCamera() {
                if (currentStream) {
                    currentStream.getTracks().forEach(track => track.stop());
                    currentStream = null;
                    video.srcObject = null;
                }

                startBtn.disabled = false;
                stopBtn.disabled = true;
                switchBtn.style.display = 'none';

                updateStatus('Câmera parada', 'info');
            }

            async function switchCamera() {
                if (!currentStream) return;

                stopCamera();
                
                // Alternar entre frontal e traseira
                currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
                
                await startCamera();
            }

            // Event listeners
            startBtn.addEventListener('click', startCamera);
            stopBtn.addEventListener('click', stopCamera);
            switchBtn.addEventListener('click', switchCamera);

            // Verificar se o navegador suporta getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                updateStatus('❌ Seu navegador não suporta acesso à câmera', 'error');
                startBtn.disabled = true;
            }

            // Listar câmeras disponíveis (para debug)
            navigator.mediaDevices.enumerateDevices()
                .then(devices => {
                    const videoDevices = devices.filter(device => device.kind === 'videoinput');
                    console.log('Câmeras disponíveis:', videoDevices.length);
                    
                    if (videoDevices.length === 0) {
                        updateStatus('❌ Nenhuma câmera encontrada', 'error');
                        startBtn.disabled = true;
                    }
                })
                .catch(err => console.error('Erro ao listar dispositivos:', err));
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/camera")
def camera():
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

threading.Thread(target=udp_receiver, daemon=True).start()
