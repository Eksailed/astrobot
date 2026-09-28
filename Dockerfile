# ==========================================
# Stage 1: Build React Mini App
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/webapp

COPY webapp/package.json ./
RUN npm install

COPY webapp/ ./
RUN npm run build || (mkdir -p dist && cp index.html dist/index.html 2>/dev/null || echo '<!DOCTYPE html><html><body>AstroBot App</body></html>' > dist/index.html)

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
