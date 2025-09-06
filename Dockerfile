FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY static/ static/

RUN mkdir -p uploads

EXPOSE 3000

CMD ["python", "main.py"]