#!/bin/bash

# Start frontend server
# Serves the frontend on http://localhost:8080

cd "$(dirname "$0")/frontend"

echo "=========================================="
echo "Starting Frontend Server"
echo "=========================================="
echo ""
echo "Frontend will be available at:"
echo "  http://localhost:8080"
echo ""
echo "Make sure the MCP server is running on:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -m http.server 8080

