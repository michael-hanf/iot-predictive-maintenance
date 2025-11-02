FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy inference service code
COPY ml/inference_service.py .

# Create models directory (will be mounted as volume in docker-compose)
RUN mkdir -p models

# Health check: service should be ready within 5 minutes (for model download)
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run the Flask service
CMD ["python", "inference_service.py"]
