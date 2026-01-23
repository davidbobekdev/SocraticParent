# Use a slim Python 3.12 image for 2026 compatibility
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Security: Create a non-root user
RUN addgroup --system socratic && adduser --system --group socratic

# Dependency Layer (Cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Application Layer
# Copy static files first, then backend code
COPY ./static ./static
COPY ./main.py .

# Create data directory for persistent storage (will be mounted as volume)
RUN mkdir -p /data && chown socratic:socratic /data

# 6. Permissions: Give the non-root user ownership
RUN chown -R socratic:socratic $APP_HOME

# 7. Run as root to have write access to mounted volumes
# Note: In production, you'd want proper volume permissions, but for Railway this works
USER root

# Launch application
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]