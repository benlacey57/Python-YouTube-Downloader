#!/bin/bash

# Cron Installation Script
# Sets up automated cron jobs for YouTube Playlist Downloader

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Check if cron is installed
check_cron() {
    if ! command -v crontab &> /dev/null; then
        print_error "cron is not installed!"
        echo "Install with: sudo apt install cron (Ubuntu/Debian)"
        exit 1
    fi
    print_success "cron is installed"
}

# Make scripts executable
setup_permissions() {
    print_info "Setting up file permissions..."
    chmod +x "$SCRIPT_DIR/cron.py"
    print_success "Permissions set"
}

# Display current crontab
show_current_crontab() {
    print_info "Current crontab:"
    echo "----------------------------------------"
    crontab -l 2>/dev/null || echo "(No crontab configured)"
    echo "----------------------------------------"
    echo ""
}

# Install cron job
install_cron_job() {
    local schedule=$1
    local options=$2
    local description=$3
    
    # Create temp file
    local temp_cron=$(mktemp)
    
    # Export current crontab
    crontab -l > "$temp_cron" 2>/dev/null || true
    
    # Add comment
    echo "" >> "$temp_cron"
    echo "# YouTube Playlist Downloader - $description" >> "$temp_cron"
    
    # Add cron job
    echo "$schedule cd $PROJECT_DIR && /usr/bin/python3 scripts/cron.py $options >> logs/cron.log 2>&1" >> "$temp_cron"
    
    # Install new crontab
    crontab "$temp_cron"
    
    # Cleanup
    rm "$temp_cron"
    
    print_success "Installed: $description"
}

# Main menu
main_menu() {
    print_header "Cron Job Installer"
    
    echo "Select cron job schedule:"
    echo ""
    echo "  1) Every hour - Check channels and download"
    echo "  2) Every 6 hours - Check channels and download"
    echo "  3) Every 12 hours - Check channels and download"
    echo "  4) Daily at midnight - Check channels and download"
    echo "  5) Daily at 2 AM - Check channels and download"
    echo "  6) Check channels only (every hour)"
    echo "  7) Download queues only (every 3 hours)"
    echo "  8) Custom schedule"
    echo "  9) Install multiple jobs"
    echo "  10) Remove all YouTube Playlist Downloader jobs"
    echo "  11) View current crontab"
    echo "  12) Exit"
    echo ""
    
    read -p "Choice [1-12]: " choice
    
    case $choice in
        1)
            install_cron_job "0 * * * *" "" "Every hour - Full run"
            ;;
        2)
            install_cron_job "0 */6 * * *" "" "Every 6 hours - Full run"
            ;;
        3)
            install_cron_job "0 */12 * * *" "" "Every 12 hours - Full run"
            ;;
        4)
            install_cron_job "0 0 * * *" "" "Daily at midnight - Full run"
            ;;
        5)
            install_cron_job "0 2 * * *" "" "Daily at 2 AM - Full run"
            ;;
        6)
            install_cron_job "0 * * * *" "--check-only" "Every hour - Check channels only"
            ;;
        7)
            install_cron_job "0 */3 * * *" "--download-only" "Every 3 hours - Download only"
            ;;
        8)
            custom_schedule
            ;;
        9)
            install_multiple
            ;;
        10)
            remove_jobs
            ;;
        11)
            show_current_crontab
            read -p "Press Enter to continue..."
            main_menu
            ;;
        12)
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            main_menu
            ;;
    esac
}

# Custom schedule
custom_schedule() {
    print_header "Custom Schedule"
    
    echo "Cron schedule format:"
    echo "  * * * * *"
    echo "  │ │ │ │ │"
    echo "  │ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)"
    echo "  │ │ │ └───── Month (1-12)"
    echo "  │ │ └─────── Day of month (1-31)"
    echo "  │ └───────── Hour (0-23)"
    echo "  └─────────── Minute (0-59)"
    echo ""
    echo "Examples:"
    echo "  0 * * * *     Every hour"
    echo "  */15 * * * *  Every 15 minutes"
    echo "  0 0 * * *     Daily at midnight"
    echo "  0 */6 * * *   Every 6 hours"
    echo "  0 9 * * 1     Every Monday at 9 AM"
    echo ""
    
    read -p "Enter cron schedule: " schedule
    
    echo ""
    echo "Options:"
    echo "  1) Full run (check channels + download)"
    echo "  2) Check channels only"
    echo "  3) Download only"
    echo "  4) Custom options"
    read -p "Choice [1-4]: " opt_choice
    
    case $opt_choice in
        1)
            options=""
            desc="Full run"
            ;;
        2)
            options="--check-only"
            desc="Check channels only"
            ;;
        3)
            options="--download-only"
            desc="Download only"
            ;;
        4)
            read -p "Enter options: " options
            desc="Custom options"
            ;;
        *)
            print_error "Invalid choice"
            return
            ;;
    esac
    
    install_cron_job "$schedule" "$options" "$desc"
}

# Install multiple jobs
install_multiple() {
    print_header "Install Multiple Jobs"
    
    echo "Common setup: Check every hour, download every 3 hours"
    echo ""
    
    if [ "$(ask_yes_no "Install this setup?")" = "yes" ]; then
        install_cron_job "0 * * * *" "--check-only" "Hourly - Check channels"
        install_cron_job "0 */3 * * *" "--download-only" "Every 3 hours - Download queues"
        print_success "Multiple jobs installed!"
    fi
}

# Remove jobs
remove_jobs() {
    print_header "Remove Cron Jobs"
    
    echo "This will remove ALL YouTube Playlist Downloader cron jobs"
    echo ""
    
    if [ "$(ask_yes_no "Continue?")" = "yes" ]; then
        # Create temp file
        temp_cron=$(mktemp)
        
        # Export current crontab without YouTube Playlist Downloader jobs
        crontab -l 2>/dev/null | grep -v "YouTube Playlist Downloader" | grep -v "scripts/cron.py" > "$temp_cron" || true
        
        # Install cleaned crontab
        crontab "$temp_cron"
        
        # Cleanup
        rm "$temp_cron"
        
        print_success "All YouTube Playlist Downloader cron jobs removed"
    fi
}

# Ask yes/no question
ask_yes_no() {
    local question=$1
    read -p "$question [y/N]: " response
    case $response in
        [Yy]* ) echo "yes";;
        * ) echo "no";;
    esac
}

# Test cron script
test_cron() {
    print_header "Testing Cron Script"
    
    print_info "Running test..."
    cd "$PROJECT_DIR"
    python3 scripts/cron.py --no-notify
    
    if [ $? -eq 0 ]; then
        print_success "Test completed successfully!"
        echo ""
        print_info "Check logs/cron.log for details"
    else
        print_error "Test failed!"
        exit 1
    fi
}

# Setup email notifications for cron
setup_email_notifications() {
    print_header "Setup Cron Email Notifications"
    
    echo "Cron can send email notifications on errors"
    echo ""
    
    if [ "$(ask_yes_no "Setup email notifications?")" = "yes" ]; then
        read -p "Enter email address: " email
        
        temp_cron=$(mktemp)
        
        # Add MAILTO at top of crontab
        echo "MAILTO=$email" > "$temp_cron"
        crontab -l 2>/dev/null >> "$temp_cron" || true
        
        crontab "$temp_cron"
        rm "$temp_cron"
        
        print_success "Email notifications configured for: $email"
    fi
}

# Main execution
main() {
    cd "$PROJECT_DIR"
    
    # Check requirements
    check_cron
    setup_permissions
    
    # Show current crontab
    show_current_crontab
    
    # Test option
    if [ "$1" = "--test" ]; then
        test_cron
        exit 0
    fi
    
    # Show menu
    main_menu
    
    echo ""
    print_success "Cron jobs configured!"
    echo ""
    print_info "Useful commands:"
    echo "  crontab -l          View installed cron jobs"
    echo "  crontab -e          Edit cron jobs manually"
    echo "  tail -f logs/cron.log   Watch cron log in real-time"
    echo ""
    print_info "To test manually:"
    echo "  python3 scripts/cron.py"
    echo ""
}

# Run main
main "$@"
