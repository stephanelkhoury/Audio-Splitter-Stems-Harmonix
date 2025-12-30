#!/bin/bash

#=============================================================================
# Harmonix Audio Splitter - Start Script
# Version: 1.1.0
# Date: December 30, 2025
# Author: Stephane El Khoury
#=============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"
LOG_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"
PID_FILE="$PROJECT_ROOT/.harmonix.pid"

# Configuration
PORT=${PORT:-5001}
HOST=${HOST:-"0.0.0.0"}

#=============================================================================
# Helper Functions
#=============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║   🎵  HARMONIX AUDIO SPLITTER                                     ║"
    echo "║       AI-Powered Stem Separation                                  ║"
    echo "║                                                                   ║"
    echo "║   Version: 1.1.0                                                  ║"
    echo "║   Date: December 30, 2025                                         ║"
    echo "║   Author: Stephane El Khoury                                      ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 is installed"
        return 0
    else
        log_error "$1 is NOT installed"
        return 1
    fi
}

check_python_package() {
    if python -c "import $1" 2>/dev/null; then
        log_success "Python package '$1' is available"
        return 0
    else
        log_error "Python package '$1' is NOT available"
        return 1
    fi
}

#=============================================================================
# Pre-flight Checks
#=============================================================================

preflight_checks() {
    echo ""
    log_info "Running pre-flight checks..."
    echo ""
    
    local errors=0
    
    # Check Python
    echo -e "${CYAN}=== System Requirements ===${NC}"
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION"
    else
        ((errors++))
    fi
    
    # Check ffmpeg
    if ! check_command ffmpeg; then
        log_warning "ffmpeg is required for audio processing"
        log_info "Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
        ((errors++))
    fi
    
    # Check pip
    check_command pip3 || ((errors++))
    
    echo ""
    echo -e "${CYAN}=== Virtual Environment ===${NC}"
    
    # Check virtual environment
    if [ -d "$VENV_DIR" ]; then
        log_success "Virtual environment exists at $VENV_DIR"
    else
        log_warning "Virtual environment not found"
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
    
    echo ""
    echo -e "${CYAN}=== Python Dependencies ===${NC}"
    
    # Check critical Python packages
    check_python_package flask || ((errors++))
    check_python_package werkzeug || ((errors++))
    check_python_package torch || log_warning "PyTorch not installed (needed for stem separation)"
    check_python_package demucs || log_warning "Demucs not installed (needed for stem separation)"
    check_python_package whisper || log_warning "Whisper not installed (needed for lyrics extraction)"
    check_python_package librosa || log_warning "Librosa not installed (needed for audio analysis)"
    check_python_package pydub || ((errors++))
    
    echo ""
    echo -e "${CYAN}=== Directory Structure ===${NC}"
    
    # Create required directories
    for dir in "$LOG_DIR" "$DATA_DIR" "$DATA_DIR/uploads" "$DATA_DIR/outputs" "$DATA_DIR/temp" "$PROJECT_ROOT/models"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        else
            log_success "Directory exists: $dir"
        fi
    done
    
    # Check users.json
    if [ ! -f "$DATA_DIR/users.json" ]; then
        log_warning "users.json not found, creating default..."
        echo '{"users": {}}' > "$DATA_DIR/users.json"
        log_success "Created default users.json"
    fi
    
    echo ""
    
    if [ $errors -gt 0 ]; then
        log_error "Pre-flight checks failed with $errors error(s)"
        log_info "Please fix the issues above and try again"
        echo ""
        log_info "To install missing packages, run:"
        echo "    pip install -r requirements.txt"
        echo ""
        return 1
    fi
    
    log_success "All pre-flight checks passed!"
    return 0
}

#=============================================================================
# Start Application
#=============================================================================

start_application() {
    echo ""
    log_info "Starting Harmonix Audio Splitter..."
    echo ""
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log_warning "Harmonix is already running (PID: $OLD_PID)"
            log_info "Use './scripts/stop.sh' to stop it first"
            return 1
        else
            log_info "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Set environment variables
    export FLASK_ENV=${FLASK_ENV:-development}
    export FLASK_DEBUG=${FLASK_DEBUG:-0}
    export PORT=$PORT
    
    # Create log file
    LOG_FILE="$LOG_DIR/harmonix_$(date +%Y%m%d_%H%M%S).log"
    
    # Start the application
    log_info "Starting server on http://$HOST:$PORT"
    log_info "Log file: $LOG_FILE"
    echo ""
    
    # Run in background and save PID
    nohup python run_dashboard.py > "$LOG_FILE" 2>&1 &
    APP_PID=$!
    echo $APP_PID > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 2
    
    # Check if started successfully
    if ps -p "$APP_PID" > /dev/null 2>&1; then
        echo ""
        log_success "Harmonix Audio Splitter started successfully!"
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "  ${GREEN}🌐 Access the application at:${NC}"
        echo -e "     ${PURPLE}http://localhost:$PORT${NC}"
        echo ""
        echo -e "  ${GREEN}📋 Default admin credentials:${NC}"
        echo -e "     Email: ${CYAN}admin@harmonix.app${NC}"
        echo -e "     Password: ${CYAN}admin123${NC}"
        echo ""
        echo -e "  ${GREEN}📁 Log file:${NC}"
        echo -e "     ${CYAN}$LOG_FILE${NC}"
        echo ""
        echo -e "  ${GREEN}🛑 To stop the server:${NC}"
        echo -e "     ${CYAN}./scripts/stop.sh${NC}"
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
        echo ""
    else
        log_error "Failed to start application"
        log_info "Check the log file for details: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

#=============================================================================
# Main
#=============================================================================

main() {
    print_banner
    
    if preflight_checks; then
        start_application
    else
        exit 1
    fi
}

# Run main function
main "$@"
