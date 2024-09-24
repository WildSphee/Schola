#!/bin/bash

# Script to start the FastAPI server

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null
then
    echo "uvicorn could not be found, installing it..."
    pip install uvicorn
fi

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8080 --reload