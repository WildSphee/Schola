#!/bin/bash

# Check if the .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    exit 1
fi

# Load environment variables from the .env file
export $(grep -v '^#' .env | xargs)

# Start the server using python3
python app.py