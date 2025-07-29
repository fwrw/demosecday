# Use uma imagem base Python com suporte a OpenCV
FROM python:3.11-slim

# Instalar dependências do sistema necessárias para OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY server.py .

# Expor a porta que a aplicação irá usar
EXPOSE 8000

# Comando para executar a aplicação
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
