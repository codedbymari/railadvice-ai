FROM python:3.11-slim

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create user and directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /tmp/transformers_cache /tmp/huggingface_cache && \
    chown -R appuser:appuser /app /tmp/transformers_cache /tmp/huggingface_cache

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app:/app/src
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV HF_HOME=/tmp/huggingface_cache

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list && \
    python -c "import uvicorn; print('uvicorn imported successfully')" && \
    python -c "import fastapi; print('fastapi imported successfully')"

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start FastAPI with uvicorn (use python -m to ensure it's found)  
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]