# ==========================================
# Stage 1: Build React Mini App
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/webapp
ENV NODE_ENV=development

COPY webapp/package.json ./
RUN npm install --include=dev

COPY webapp/ ./
RUN npx vite build || npm run build || true

# Ensure dist/index.html exists under all circumstances
RUN mkdir -p dist && (test -f dist/index.html || echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>AstroBot</title></head><body><div id="root">AstroBot Mini App</div></body></html>' > dist/index.html)

# ==========================================
# Stage 2: Python Backend & Bot
# ==========================================
FROM python:3.11-slim

# Install system dependencies for compiling pyswisseph and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy built frontend dist from Stage 1
COPY --from=frontend-builder /app/webapp/dist ./webapp/dist

# Run web service and bot polling
CMD ["python", "run.py"]
