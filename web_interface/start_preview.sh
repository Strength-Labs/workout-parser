#!/bin/bash

echo "🚀 Turnkey Coach Tools - Web Interface Preview"
echo "=============================================="
echo ""
echo "📋 Prerequisites:"
echo "   pip install fastapi uvicorn jinja2"
echo ""

# Change to the web_interface directory
cd "$(dirname "$0")"

# Start the FastAPI server
python3 main.py
