FROM python:3.11-slim

WORKDIR /app

# HEIC サポートに必要なライブラリをインストール
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libde265-dev \
    libx265-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY static/ static/

RUN mkdir -p uploads

EXPOSE 3000

CMD ["python", "main.py"]