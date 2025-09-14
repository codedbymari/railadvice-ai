#!/bin/bash
set -e  # Exit on any error

# Installer base requirements
echo "Installing base requirements..."
python -m pip install --user -r requirements.txt

# Check om tunge ML-pakker allerede er installert
echo "Checking for ML packages..."
if ! python -c "import torch, sentence_transformers, transformers, spacy" 2>/dev/null; then
    echo "Installing heavy ML packages..."
    python -m pip install --user torch==2.1.0 sentence-transformers==2.7.0 transformers==4.44.0 spacy==3.6.0
    
    echo "Downloading spaCy models..."
    python -m spacy download en_core_web_sm
    python -m spacy download nb_core_news_sm
else
    echo "ML packages already installed, skipping..."
fi

echo "Starting application..."
exec python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 1