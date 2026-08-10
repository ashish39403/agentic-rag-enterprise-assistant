FROM python:3.11-slim-bookworm

# Patch OS packages, then install native deps required by common Python wheels.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first so pip install is cached between code changes.
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements-prod.txt

# Copy only the backend package. UI, evals, docs, and local data stay out.
COPY app/ ./app/

ENV PORT=8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
