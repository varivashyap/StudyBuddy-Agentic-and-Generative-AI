#!/bin/bash

# MCP Server Setup Script
# This script sets up the Study Assistant MCP server on your machine

set -e  # Exit on error

echo "=========================================="
echo "Study Assistant MCP Server Setup"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Error: Python 3.8 or higher is required"
    echo "   Current version: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "aivenv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv aivenv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source aivenv/bin/activate

# Install/upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install base requirements
echo ""
echo "Installing base requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ Base requirements installed"
else
    echo "❌ Error: requirements.txt not found"
    exit 1
fi

# Install MCP server specific requirements
echo ""
echo "Installing MCP server requirements..."
pip install flask flask-cors werkzeug
echo "✓ MCP server requirements installed"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/uploads
mkdir -p data/cache
mkdir -p data/outputs
mkdir -p models/lora_adapters
mkdir -p results/testing
mkdir -p logs
echo "✓ Directories created"

# Check if model exists
echo ""
echo "Checking for LLM model..."
MODEL_PATH="models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
if [ -f "$MODEL_PATH" ]; then
    echo "✓ Model found: $MODEL_PATH"
else
    echo "⚠ Warning: Model not found at $MODEL_PATH"
    echo "   Please download the model using:"
    echo "   make download-model"
    echo "   or manually download from Hugging Face"
fi

# Create systemd service file (optional)
echo ""
read -p "Do you want to create a systemd service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/study-assistant-mcp.service"
    
    echo "Creating systemd service file..."
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Study Assistant MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/aivenv/bin"
ExecStart=$SCRIPT_DIR/aivenv/bin/python -m mcp_server.server --host 0.0.0.0 --port 5000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "✓ Systemd service created"
    echo ""
    echo "To enable and start the service:"
    echo "  sudo systemctl enable study-assistant-mcp"
    echo "  sudo systemctl start study-assistant-mcp"
    echo "  sudo systemctl status study-assistant-mcp"
fi

# Create start script
echo ""
echo "Creating start script..."
cat > start_mcp_server.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source aivenv/bin/activate
python -m mcp_server.server --host 0.0.0.0 --port 5000
EOF
chmod +x start_mcp_server.sh
echo "✓ Start script created: start_mcp_server.sh"

# Create stop script
cat > stop_mcp_server.sh <<'EOF'
#!/bin/bash
pkill -f "mcp_server.server"
echo "MCP server stopped"
EOF
chmod +x stop_mcp_server.sh
echo "✓ Stop script created: stop_mcp_server.sh"

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the MCP server:"
echo "  ./start_mcp_server.sh"
echo ""
echo "Or manually:"
echo "  source aivenv/bin/activate"
echo "  python -m mcp_server.server"
echo ""
echo "The server will be available at:"
echo "  http://localhost:5000"
echo ""
echo "API Endpoints:"
echo "  GET  /health           - Health check"
echo "  GET  /models           - List available models"
echo "  GET  /request-types    - List request types"
echo "  POST /upload           - Upload a document"
echo "  POST /process          - Process a document"
echo "  POST /batch-process    - Process with multiple request types"
echo ""

