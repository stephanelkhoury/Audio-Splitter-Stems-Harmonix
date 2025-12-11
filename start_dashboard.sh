#!/bin/bash
# Harmonix Dashboard Launcher

echo "=========================================="
echo "  🎵 Harmonix Audio Splitter Dashboard"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found!"
    echo "   Run ./quickstart.sh first to set up the environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip install flask flask-cors > /dev/null 2>&1
    echo "✓ Flask installed"
fi

echo "🚀 Starting Harmonix Dashboard..."
echo ""
echo "   Open your browser to:"
echo "   👉 http://localhost:5000"
echo ""
echo "   Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Start the dashboard
python -m harmonix_splitter.dashboard
