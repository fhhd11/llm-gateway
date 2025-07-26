# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with Gunicorn for multi-worker mode
# -w 4: 4 worker processes
# -k uvicorn.workers.UvicornWorker: Use Uvicorn worker class
# --bind 0.0.0.0:8000: Bind to all interfaces on port 8000
# --max-requests 1000: Restart workers after 1000 requests to prevent memory leaks
# --max-requests-jitter 100: Add jitter to prevent all workers restarting at once
# --timeout 120: Worker timeout for long-running requests
# --keep-alive 5: Keep-alive timeout
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "120", "--keep-alive", "5", "app.main:app"]
