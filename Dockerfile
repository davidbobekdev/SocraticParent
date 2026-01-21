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
# Copy static files (HTML/JS) and the backend code
COPY ./static ./static
COPY ./main.py .

# 6. Permissions: Give the non-root user ownership
RUN chown -R socratic:socratic $APP_HOME

# 7. Health Check: Ensures the app is responding
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

# 8. Switch to Secure User
USER socratic

# Launch application
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]