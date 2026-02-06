# Use a slim Python 3.12 image for 2026 compatibility
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Dependency Layer (Cached) - This layer should rarely change
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application Layer - Only copy what's needed
COPY ./static ./static
COPY ./main.py .

# Create data directory for persistent storage
RUN mkdir -p /data

# Launch application directly (simpler, faster startup)
EXPOSE 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}