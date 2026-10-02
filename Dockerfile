# Multi-stage Dockerfile for FasalSetu (SIH26033)
# Stage 1: Build React/Vite Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Runtime with LightGBM and FastAPI
FROM python:3.12-slim AS runner
WORKDIR /app

# Install libgomp1 required for LightGBM OpenMP support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install backend Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and processed data/models
COPY backend/ ./backend/

# Copy built frontend SPA assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV PYTHONPATH=/app/backend \
    STATIC_DIR=/app/frontend/dist \
    APP_ENV=production \
    DEMO_MODE=true \
    PORT=8000

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "if [ \"$DEMO_MODE\" = \"true\" ] && [ ! -f /app/backend/data/app.db ]; then python -m scripts.setup_demo --no-retrain; fi && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
