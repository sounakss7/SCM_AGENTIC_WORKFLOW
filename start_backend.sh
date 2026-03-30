#!/bin/bash

# Backend startup script
# This script starts the FastAPI backend server

cd "$(dirname "$0")"/backend

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Start the FastAPI server
echo "Starting FastAPI backend on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
