#!/bin/bash

# Installation script for YouTube Playlist Downloader

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Check FFmpeg
check_ffmpeg() {
    print_info "Checking FFmpeg..."
    
    if ! command -v ffmpeg &> /dev/null; then
        print_warning "FFmpeg is not installed"
        echo ""
        echo "FFmpeg is required for audio extraction and video merging"
        echo ""
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt install ffmpeg"
        echo "  macOS: brew install ffmpeg"
        echo "  Windows: Download from https://ffmpeg.org"
        echo ""
        read -p "Continue without FFmpeg? [y/N]: " response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
        print_success "FFmpeg $FFMPEG_VERSION detected"
    fi
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Recreate? [y/N]: " response
        if [[ $response =~ ^[Yy]$ ]]; then
            rm -rf venv
            python3 -m venv venv
            print_success "Virtual environment recreated"
        fi
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Install dependencies
install_deps() {
    print_info "Installing dependencies..."
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create directories
create_dirs() {
    print_info "Creating directories..."
    
    mkdir -p downloads
    mkdir -p logs
    mkdir -p data
    mkdir -p seeds
    
    print_success "Directories created"
}

# Create example seeds
create_seeds() {
    print_info "Creating example seed files..."
    
    python3 -c "from utils.database_seeder import create_example_seeds; create_example_seeds()"
    
    print_success "Example seeds created"
}

# Make scripts executable
setup_scripts() {
    print_info "Setting up scripts..."
    
    chmod +x scripts/*.sh scripts/*.py 2>/dev/null || true
    
    print_success "Scripts configured"
}

# Main installation
main() {
    print_header "YouTube Playlist Downloader - Installation"
    
    check_python
    check_ffmpeg
    create_venv
    install_deps
    create_dirs
    create_seeds
    setup_scripts
    
    print_header "Installation Complete!"
    
    echo "Next steps:"
    echo ""
    echo "  1. Activate virtual environment:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. Run the application:"
    echo "     python main.py"
    echo ""
    echo "  3. Optional - Install cron jobs:"
    echo "     bash scripts/install_cron.sh"
    echo ""
    
    print_success "Ready to go!"
}

# Run installation
main
