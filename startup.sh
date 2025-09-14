#!/bin/bash
set -e  # Exit on any error

echo "========================================="
echo "Starting application setup..."
echo "========================================="

# Install requests first for healthcheck
echo "Installing requests for healthcheck..."
python -m pip install --user requests

# Installer base requirements
echo "Installing base requirements..."
python -m pip install --user -r requirements.txt
echo "Base requirements installed successfully!"

# Check om tunge ML-pakker allerede er installert
echo "Checking for ML packages..."
if ! python -c "import torch, sentence_transformers, transformers, spacy" 2>/dev/null; then
    echo "ML packages not found. Installing heavy ML packages..."
    echo "This may take several minutes on first startup..."
    
    python -m pip install --user torch==2.1.0 sentence-transformers==2.7.0 transformers==4.44.0 spacy==3.6.0
    echo "ML packages installed successfully!"
    
    echo "Downloading spaCy models..."
    python -m spacy download en_core_web_sm
    python -m spacy download nb_core_news_sm
    echo "spaCy models downloaded successfully!"
else
    echo "ML packages already installed, skipping..."
fi

echo "========================================="
echo "Starting FastAPI application..."
echo "========================================="

# Start the application
exec python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 1