#!/bin/bash
# ==============================================================================
#  🎵 Harmonix Audio Splitter - Quick Start Script
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo ""
echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║${NC}  ${CYAN}🎵 Harmonix Audio Splitter${NC}                                  ${PURPLE}║${NC}"
echo -e "${PURPLE}║${NC}     Professional AI-Powered Stem Separation                   ${PURPLE}║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
PORT=${PORT:-5001}
HOST=${HOST:-127.0.0.1}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$PROJECT_DIR"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Function to kill existing process on port
kill_existing() {
    if check_port; then
        echo -e "${YELLOW}⚠️  Port $PORT is in use. Stopping existing process...${NC}"
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✓ Port $PORT cleared${NC}"
    fi
}

# Function to find virtual environment
find_venv() {
    if [ -d ".venv" ]; then
        echo ".venv"
    elif [ -d "venv" ]; then
        echo "venv"
    else
        echo ""
    fi
}

# Function to activate virtual environment
activate_venv() {
    local venv_dir=$(find_venv)
    
    if [ -z "$venv_dir" ]; then
        echo -e "${YELLOW}⚠️  No virtual environment found${NC}"
        echo -e "${CYAN}   Creating virtual environment...${NC}"
        python3 -m venv .venv
        venv_dir=".venv"
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    echo -e "${CYAN}📦 Activating virtual environment ($venv_dir)...${NC}"
    source "$venv_dir/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
}

# Function to check and install dependencies
check_dependencies() {
    echo -e "${CYAN}🔍 Checking dependencies...${NC}"
    
    # Check for Flask
    if ! python -c "import flask" 2>/dev/null; then
        echo -e "${YELLOW}   Installing Flask...${NC}"
        pip install flask flask-cors >/dev/null 2>&1
    fi
    
    # Check if package is installed
    if ! python -c "import harmonix_splitter" 2>/dev/null; then
        echo -e "${YELLOW}   Installing harmonix_splitter package...${NC}"
        pip install -e . >/dev/null 2>&1 || {
            # If editable install fails, add src to PYTHONPATH
            export PYTHONPATH="${PYTHONPATH}:${PROJECT_DIR}/src"
        }
    fi
    
    echo -e "${GREEN}✓ Dependencies ready${NC}"
}

# Function to ensure data directories exist
setup_directories() {
    mkdir -p data/uploads data/outputs data/temp/uploads logs models config
    echo -e "${GREEN}✓ Directories ready${NC}"
}

# Main startup
main() {
    echo -e "${BLUE}Starting Harmonix...${NC}"
    echo ""
    
    # Kill any existing process
    kill_existing
    
    # Activate virtual environment
    activate_venv
    
    # Check dependencies
    check_dependencies
    
    # Setup directories
    setup_directories
    
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "   ${CYAN}🚀 Dashboard starting...${NC}"
    echo ""
    echo -e "   ${GREEN}🌐 Local:${NC}   http://localhost:$PORT"
    echo -e "   ${GREEN}🌐 Network:${NC} http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo "$HOST"):$PORT"
    echo ""
    echo -e "   ${YELLOW}📋 Default Login:${NC}"
    echo -e "      Username: ${CYAN}admin${NC}"
    echo -e "      Password: ${CYAN}admin123${NC}"
    echo ""
    echo -e "   ${PURPLE}Press Ctrl+C to stop the server${NC}"
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Start the dashboard
    export FLASK_ENV=development
    export PYTHONPATH="${PYTHONPATH}:${PROJECT_DIR}/src"
    
    python -m harmonix_splitter.dashboard
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: ./start.sh [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --port PORT    Set custom port (default: 5001)"
        echo "  --kill         Kill existing server and exit"
        echo "  --status       Check if server is running"
        echo ""
        echo "Environment Variables:"
        echo "  PORT           Server port (default: 5001)"
        echo "  HOST           Server host (default: 127.0.0.1)"
        exit 0
        ;;
    --port)
        PORT=${2:-5001}
        main
        ;;
    --kill)
        kill_existing
        echo -e "${GREEN}✓ Server stopped${NC}"
        exit 0
        ;;
    --status)
        if check_port; then
            echo -e "${GREEN}✓ Server is running on port $PORT${NC}"
            lsof -i :$PORT
        else
            echo -e "${YELLOW}Server is not running${NC}"
        fi
        exit 0
        ;;
    *)
        main
        ;;
esac
