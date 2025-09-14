#!/bin/bash
set -e  # Exit on any error

echo "========================================="
echo "Starting application setup..."
echo "========================================="

# Set PATH to include user-installed packages - THIS IS THE KEY FIX
export PATH="/home/appuser/.local/bin:$PATH"

# Install basic requirements FIRST (including uvicorn)
echo "Installing base requirements..."
python -m pip install --user -r requirements.txt
echo "Base requirements installed successfully!"

# Verify uvicorn is available
echo "Verifying uvicorn installation..."
python -c "import uvicorn; print('uvicorn available')" || {
    echo "uvicorn not found, installing directly..."
    python -m pip install --user uvicorn[standard]==0.24.0
}

# Check if ML packages are already installed
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

# Start the application (uvicorn is now installed and in PATH)
exec python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 1