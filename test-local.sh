#!/bin/bash
# Script para testar o container localmente

echo "Construindo a imagem Docker..."
docker build -t camera-server .

echo "Executando o container..."
docker run -p 8000:8000 -p 5000:5000/udp camera-server

echo "Acesse http://localhost:8000 para ver a API"
echo "Stream de câmera disponível em http://localhost:8000/camera"
