#!/bin/bash

# Load environment variables from .env
export $(grep -v '^#' .env | xargs)

cd "$(dirname "$0")/.." || { echo "Project root directory not found"; exit 1; }
. .venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Run the FastAPI server from root on the specified port, 8000 by default
uvicorn api.files:app --host 0.0.0.0 --port ${API_SERVER_PORT:-8000} || { echo "Failed to start the server"; exit 1; }

echo "Server running at http://localhost:${API_SERVER_PORT:-8000}"