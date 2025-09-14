# --------------------------
# Builder stage
# --------------------------
FROM python:3.11-slim as builder

# Install build tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------
# Production stage
# --------------------------
FROM python:3.11-slim

# Install runtime deps only
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app /tmp/uploads /data \
    && chown -R appuser:appuser /app /tmp/uploads /data

WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Environment variables for lazy loading
ENV ANONYMIZED_TELEMETRY=False
ENV CHROMA_SERVER_NOFILE=1
ENV TOKENIZERS_PARALLELISM=false
ENV DATA_PATH=/data

# Expose port
EXPOSE 8000

# Healthcheck for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start FastAPI app with single worker for Railway
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
