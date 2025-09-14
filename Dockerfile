# ==============================
# Production stage with runtime installation
# ==============================
FROM python:3.11-slim

# Sett miljøvariabler
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer runtime-avhengigheter
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Opprett appuser og mapper med riktige permissions
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /tmp/uploads /data /home/appuser/.cache && \
    chown -R appuser:appuser /app /tmp/uploads /data /home/appuser

WORKDIR /app

# Kopier app-kode først
COPY --chown=appuser:appuser . .

# Sett executable permission på startup script
RUN chmod +x startup.sh

# Switch til ikke-root bruker
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start med startup script som installerer pakker hvis nødvendig
CMD ["./startup.sh"]