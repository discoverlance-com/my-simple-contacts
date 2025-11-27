# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=main.py \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install production WSGI server
RUN pip install gunicorn

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application with Gunicorn optimized for Cloud Run and Cloud SQL connection stability
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--worker-class", "sync", "--timeout", "45", "--keep-alive", "2", "--max-requests", "100", "--max-requests-jitter", "10", "--graceful-timeout", "30", "main:app"]