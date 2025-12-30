#!/bin/bash

#=============================================================================
# Harmonix Audio Splitter - Stop Script
# Version: 1.1.0
# Date: December 30, 2025
# Author: Stephane El Khoury
#=============================================================================

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
DATA_DIR="$PROJECT_ROOT/data"
BACKUP_DIR="$PROJECT_ROOT/backups"
PID_FILE="$PROJECT_ROOT/.harmonix.pid"

#=============================================================================
# Helper Functions
#=============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║   🎵  HARMONIX AUDIO SPLITTER - SHUTDOWN                          ║"
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

#=============================================================================
# Backup Functions
#=============================================================================

create_backup() {
    log_info "Creating backup of all data..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup filename with timestamp
    BACKUP_NAME="harmonix_backup_$(date +%Y%m%d_%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    # Create temporary directory for backup
    mkdir -p "$BACKUP_PATH"
    
    # Copy data directory
    if [ -d "$DATA_DIR" ]; then
        cp -r "$DATA_DIR" "$BACKUP_PATH/data"
        log_success "Backed up data directory"
    fi
    
    # Copy config
    if [ -d "$PROJECT_ROOT/config" ]; then
        cp -r "$PROJECT_ROOT/config" "$BACKUP_PATH/config"
        log_success "Backed up config directory"
    fi
    
    # Copy logs (last 5 log files only)
    if [ -d "$PROJECT_ROOT/logs" ]; then
        mkdir -p "$BACKUP_PATH/logs"
        ls -t "$PROJECT_ROOT/logs"/*.log 2>/dev/null | head -5 | while read log; do
            cp "$log" "$BACKUP_PATH/logs/"
        done
        log_success "Backed up recent log files"
    fi
    
    # Create the ZIP archive
    cd "$BACKUP_DIR"
    zip -r "$BACKUP_NAME.zip" "$BACKUP_NAME" > /dev/null 2>&1
    
    # Remove temporary directory
    rm -rf "$BACKUP_PATH"
    
    FINAL_BACKUP="$BACKUP_DIR/$BACKUP_NAME.zip"
    BACKUP_SIZE=$(du -h "$FINAL_BACKUP" | cut -f1)
    
    log_success "Backup created: $FINAL_BACKUP ($BACKUP_SIZE)"
    
    # Clean old backups (keep last 10)
    cd "$BACKUP_DIR"
    ls -t *.zip 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
    
    return 0
}

#=============================================================================
# Stop Application
#=============================================================================

stop_application() {
    echo ""
    log_info "Stopping Harmonix Audio Splitter..."
    echo ""
    
    local stopped=0
    
    # Method 1: Use PID file
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "Found running process (PID: $PID)"
            
            # Send SIGTERM for graceful shutdown
            kill -TERM "$PID" 2>/dev/null
            
            # Wait for process to stop
            log_info "Waiting for graceful shutdown..."
            for i in {1..10}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    stopped=1
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if [ $stopped -eq 0 ]; then
                log_warning "Process not responding, forcing shutdown..."
                kill -9 "$PID" 2>/dev/null
                sleep 1
                stopped=1
            fi
            
            log_success "Process stopped"
        else
            log_info "Process not running (stale PID file)"
        fi
        rm -f "$PID_FILE"
    fi
    
    # Method 2: Find by port
    PORT_PID=$(lsof -t -i:5001 2>/dev/null | head -1)
    if [ -n "$PORT_PID" ]; then
        log_info "Found process on port 5001 (PID: $PORT_PID)"
        kill -TERM "$PORT_PID" 2>/dev/null
        sleep 2
        
        if ps -p "$PORT_PID" > /dev/null 2>&1; then
            kill -9 "$PORT_PID" 2>/dev/null
        fi
        
        log_success "Stopped process on port 5001"
        stopped=1
    fi
    
    # Method 3: Find by process name
    FLASK_PIDS=$(pgrep -f "run_dashboard.py" 2>/dev/null)
    if [ -n "$FLASK_PIDS" ]; then
        log_info "Found Flask processes: $FLASK_PIDS"
        echo "$FLASK_PIDS" | while read pid; do
            kill -TERM "$pid" 2>/dev/null
        done
        sleep 2
        
        # Force kill remaining
        echo "$FLASK_PIDS" | while read pid; do
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null
            fi
        done
        
        log_success "Stopped Flask processes"
        stopped=1
    fi
    
    if [ $stopped -eq 0 ]; then
        log_info "No running Harmonix processes found"
    fi
    
    return 0
}

#=============================================================================
# Cleanup
#=============================================================================

cleanup_temp_files() {
    log_info "Cleaning up temporary files..."
    
    # Clean temp directory
    if [ -d "$DATA_DIR/temp" ]; then
        find "$DATA_DIR/temp" -type f -mmin +60 -delete 2>/dev/null
        log_success "Cleaned temporary files older than 1 hour"
    fi
    
    # Clean upload directory (files older than 24 hours that aren't processed)
    if [ -d "$DATA_DIR/uploads" ]; then
        find "$DATA_DIR/uploads" -type f -mmin +1440 -delete 2>/dev/null
        log_success "Cleaned old upload files"
    fi
    
    return 0
}

#=============================================================================
# Main
#=============================================================================

main() {
    print_banner
    
    # Parse arguments
    SKIP_BACKUP=0
    FORCE=0
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                SKIP_BACKUP=1
                shift
                ;;
            --force|-f)
                FORCE=1
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --no-backup    Skip backup before stopping"
                echo "  --force, -f    Force stop without confirmation"
                echo "  --help, -h     Show this help message"
                echo ""
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Confirmation prompt (unless forced)
    if [ $FORCE -eq 0 ]; then
        echo ""
        read -p "Are you sure you want to stop Harmonix? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled"
            exit 0
        fi
    fi
    
    # Create backup before stopping
    if [ $SKIP_BACKUP -eq 0 ]; then
        echo ""
        create_backup
    fi
    
    # Stop the application
    echo ""
    stop_application
    
    # Cleanup
    echo ""
    cleanup_temp_files
    
    # Final message
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}✓ Harmonix Audio Splitter has been stopped${NC}"
    echo ""
    if [ $SKIP_BACKUP -eq 0 ]; then
        echo -e "  ${GREEN}📦 Backup saved to:${NC}"
        echo -e "     ${CYAN}$BACKUP_DIR/${NC}"
        echo ""
    fi
    echo -e "  ${GREEN}🚀 To start again:${NC}"
    echo -e "     ${CYAN}./scripts/start.sh${NC}"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Run main function
main "$@"
