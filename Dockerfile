FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create user early to avoid permission issues
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy requirements and install in layers for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install lightweight packages first
RUN pip install --user --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    python-dotenv==1.0.1 \
    pandas==2.1.4 \
    numpy==1.26.4 \
    requests==2.32.3 \
    aiofiles==23.2.1 \
    PyYAML==6.0.2 \
    scikit-learn==1.4.2 \
    chromadb==0.4.15

# Install CPU-only PyTorch first (much smaller/faster)
RUN pip install --user --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0+cpu

# Install other heavy ML packages with timeout handling
RUN pip install --user --no-cache-dir --timeout 600 \
    sentence-transformers==2.7.0 \
    transformers==4.44.0 \
    spacy>=3.7.0

# Download spaCy models
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download nb_core_news_sm

# Copy application code last for better layer caching
COPY --chown=appuser:appuser . .

# Ensure PATH includes user-installed packages
ENV PATH="/home/appuser/.local/bin:$PATH"

EXPOSE 8000

# Lightweight healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]