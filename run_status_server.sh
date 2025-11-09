#!/bin/bash
# Start the CyTube Bot Web Status Server
# Usage: ./run_status_server.sh [port]

PORT=${1:-5000}

echo "Starting CyTube Bot Status Server on port $PORT..."
echo ""
echo "Open your browser to: http://127.0.0.1:$PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 web/status_server.py --port "$PORT"
