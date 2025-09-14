#!/bin/bash
set -e

# Debug: Print environment variables
echo "PORT environment variable: '$PORT'"
echo "All environment variables with PORT:"
env | grep -i port || echo "No PORT variables found"

# Set default port if PORT is not set or empty
if [ -z "$PORT" ]; then
    echo "PORT not set, using default 8000"
    PORT=8000
else
    echo "Using PORT: $PORT"
fi

# Validate that PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT '$PORT' is not a valid number, using 8000"
    PORT=8000
fi

echo "Starting uvicorn on port $PORT..."
exec python -m uvicorn src.api:app --host 0.0.0.0 --port "$PORT"