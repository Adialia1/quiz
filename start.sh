#!/bin/sh
# Startup script for Railway deployment
# Ensures PORT environment variable is properly used

# Use Railway's PORT variable, default to 8000 if not set
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."

# Start uvicorn with the port
exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --workers 1 --timeout-keep-alive 300
