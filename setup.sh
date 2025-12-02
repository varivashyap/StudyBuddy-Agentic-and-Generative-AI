#!/bin/bash

# Study Assistant - Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "=========================================="
echo "Study Assistant - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo ""
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Create directories
echo ""
echo "Creating data directories..."
mkdir -p data/uploads
mkdir -p data/outputs
mkdir -p data/cache
echo "✓ Data directories created"

# Create .env file
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY (optional)"
else
    echo "✓ .env file already exists"
fi

# Run tests
echo ""
echo "Running tests..."
pytest tests/ -v || echo "⚠️  Some tests failed (this is expected if API keys are not set)"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the example: python examples/basic_usage.py"
echo "4. Or use the CLI: python -m src.cli --help"
echo ""
echo "Documentation:"
echo "- Quick Start: QUICKSTART.md"
echo "- Implementation Notes: IMPLEMENTATION_NOTES.md"
echo "- Project Status: PROJECT_STATUS.md"
echo ""

