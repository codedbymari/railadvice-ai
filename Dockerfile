# ==============================
# Builder stage (lettvekts install)
# ==============================
FROM python:3.11-slim as builder

# Sett miljøvariabler
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer kun byggeavhengigheter
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Opprett virtuell environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Kopier kun requirements
COPY requirements.txt .

# Installer kun lette pakker (ikke tunge ML-pakker)
RUN pip install --no-cache-dir -r requirements.txt

# ==============================
# Production stage
# ==============================
FROM python:3.11-slim

# Installer runtime-avhengigheter
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Kopier venv fra builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Opprett ikke-root bruker og mapper
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /tmp/uploads /data && \
    chown -R appuser:appuser /app /tmp/uploads /data

WORKDIR /app

# Kopier app-kode
COPY --chown=appuser:appuser . .

# Switch til ikke-root bruker
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Installer tunge ML-pakker runtime når container starter
# Dette skjer første gang container starter, så build holder seg under Railway timeout
RUN python -m pip install --no-cache-dir torch==2.1.0 sentence-transformers==2.7.0 transformers==4.44.0 spacy==3.6.0 && \
    python -m spacy download en_core_web_sm nb_core_news_sm

# Start app
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
