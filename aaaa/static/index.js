const video = document.getElementById('video');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');

const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');

let stream = null;
let timer = null;

let deviceId = localStorage.getItem('deviceId');
if (!deviceId) {
  deviceId = crypto.randomUUID();
  localStorage.setItem('deviceId', deviceId);
}

async function captureAndSend() {
  if (!stream) return;
   canvas.width = video.videoWidth || 320;
   canvas.height = video.videoHeight || 240;
   ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  canvas.toBlob(async (blob) => {
    try {
      const form = new FormData();
  form.append('frame', blob, 'frame.jpg');
  form.append('device_id', deviceId);
  form.append('user_agent', navigator.userAgent);
      await fetch('/upload', { method: 'POST', body: form });
      console.log('Imagem enviada via POST:', new Date().toLocaleTimeString());
    } catch (e) {
      console.error('Erro ao enviar imagem:', e);
    }
  }, 'image/jpeg', 0.7);
}

function startCaptureLoop() {
timer = setInterval(captureAndSend, 50);
  startBtn.disabled = true;
  stopBtn.disabled = false;
}

async function startCapture() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    video.srcObject = stream;
    await video.play();
    startCaptureLoop();
  } catch (err) {
    alert('Erro ao acessar câmera: ' + err.message);
    console.error(err);
  }
}

function stopCapture() {
  if (timer) clearInterval(timer);
  timer = null;
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  startBtn.disabled = false;
  stopBtn.disabled = true;
}

startBtn.addEventListener('click', startCapture);
stopBtn.addEventListener('click', stopCapture);
