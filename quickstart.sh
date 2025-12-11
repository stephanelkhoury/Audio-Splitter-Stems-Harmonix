#!/bin/bash
# Harmonix Audio Splitter - Quick Start Script

set -e

echo "============================================"
echo "  Harmonix Audio Splitter - Quick Start"
echo "============================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "Error: Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg not found. Some features may not work."
    echo "Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
    echo ""
else
    echo "✓ ffmpeg detected"
    echo ""
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Install package in development mode
echo "Installing Harmonix..."
pip install -e . > /dev/null 2>&1
echo "✓ Harmonix installed"
echo ""

# Create directories
echo "Creating directories..."
mkdir -p data/uploads data/outputs data/temp models logs
echo "✓ Directories created"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created (edit as needed)"
    echo ""
fi

echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo ""
echo "Quick Start Commands:"
echo ""
echo "  1. Test CLI:"
echo "     python -m harmonix_splitter.cli --help"
echo ""
echo "  2. Start API server:"
echo "     uvicorn harmonix_splitter.api.main:app --reload"
echo ""
echo "  3. Run tests:"
echo "     pytest"
echo ""
echo "  4. Separate audio:"
echo "     python -m harmonix_splitter.cli your_song.mp3"
echo ""
echo "For full documentation, see README.md"
echo ""
echo "Enjoy Harmonix! 🎵"
