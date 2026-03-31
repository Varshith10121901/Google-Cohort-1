# TASK: Project 1, 2 & 3 (AURA Lite Core - Containerization for Cloud Run)
# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies only (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code and data
COPY app/ ./app/
COPY data/ ./data/
COPY integrations/ ./integrations/

# Copy the frontend UI and any static background images
COPY frontend.html ./

# Ensure Python can resolve modules in /app
ENV PYTHONPATH=/app

# Cloud Run injects PORT (default 8080)
ENV PORT=8080
EXPOSE $PORT

# Run with Uvicorn using shell to evaluate $PORT. Cloud Run handles horizontal scaling (no extra workers needed)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
