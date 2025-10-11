#!/bin/bash
# Quick start script for Quiz Generator API

echo "🚀 Starting Quiz Generator & Legal Expert API..."
echo ""
echo "📚 API will be available at:"
echo "   - Base URL: http://localhost:8000"
echo "   - Interactive Docs: http://localhost:8000/docs"
echo "   - Alternative Docs: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python api/main.py
