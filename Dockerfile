# Usa uma imagem Python leve baseada em Linux (Debian)
FROM python:3.9-slim

# 1. Instala as dependências de sistema do WeasyPrint
# libpango, libcairo, libgdk-pixbuf são vitais para gerar PDF
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libmemcached-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Configura o diretório de trabalho
WORKDIR /app

# 3. Copia os arquivos de requisitos e instala
# (Crie um requirements.txt se não tiver, veja abaixo)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia o código do projeto
COPY . .

# 5. Expõe a porta e roda o servidor
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]