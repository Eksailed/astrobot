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

# Run web service and bot polling
CMD ["python", "run.py"]
