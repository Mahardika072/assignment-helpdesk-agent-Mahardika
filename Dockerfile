FROM python:3.11-slim

WORKDIR /app

# FAISS membutuhkan library OpenMP di image slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements dulu agar layer install ter-cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin source code dan data
COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]