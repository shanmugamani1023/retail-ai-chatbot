# App image (FastAPI). Used for cloud deploy (Phase 4).
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; psycopg[binary] ships its own libpq.
COPY requirements.txt .
# Install CPU-only PyTorch first so sentence-transformers doesn't pull the
# huge CUDA/GPU build (~6 GB). Keeps the image small for a CPU VM.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
