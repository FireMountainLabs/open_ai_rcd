#!/bin/bash

# AIML Database Service Startup Script

echo "Starting AIML Database Service..."
echo "================================="

# Check if database file exists
if [ ! -f "${DB_PATH:-aiml_data.db}" ]; then
    echo "❌ Error: Database file not found at ${DB_PATH:-aiml_data.db}"
    echo "   Please ensure the database file is mounted or available"
    echo "   Example: docker run -v ./aiml_data.db:/data/aiml_data.db database-service"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# Start the service
echo "Starting FastAPI service..."
echo "Database: ${DB_PATH:-aiml_data.db}"
echo "API URL: http://localhost:${API_PORT:-5001}"
echo "Health Check: http://localhost:${API_PORT:-5001}/api/health"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
