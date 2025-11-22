# Makefile Usage Guide

This project includes a comprehensive Makefile to simplify common operations.

## Quick Start

For first-time setup on a new machine:

```bash
make setup
make run
```

This will install dependencies, create the virtual environment, run migrations, and get you ready to use the application.

## Available Commands

### Installation & Setup

- **`make setup`** - Complete first-time setup (install + migrate)
- **`make install`** - Install application and dependencies
- **`make install-fresh`** - Fresh install (removes existing data directories)
- **`make migrate`** - Run database migrations
- **`make check-deps`** - Check system dependencies (Python, ffmpeg, git)

### Running the Application

- **`make run`** - Start the YouTube Playlist Downloader
- **`make status`** - Show application status (environment, config, database, backups)

### Proxy Management

- **`make load-proxies`** - Load proxies from `proxies.txt` file

### Backup & Restore

- **`make backup`** - Create timestamped backup of configuration, database, and proxies
- **`make restore`** - Restore from a previous backup (interactive)

### Development

- **`make test`** - Run test suite
- **`make lint`** - Run code linters (ruff if available)
- **`make format`** - Format code (ruff or black)

### Maintenance

- **`make clean`** - Remove cache and temporary files (`__pycache__`, `.pyc`, etc.)
- **`make uninstall`** - Uninstall application data

### Help

- **`make help`** - Show all available commands (default target)

## Examples

### First Time Setup

```bash
# Clone or download the project
cd YouTube_Playlist_Downloader

# Complete setup
make setup

# Start the application
make run
```

### Regular Usage

```bash
# Check status
make status

# Run the application
make run
```

### Backup Before Major Changes

```bash
# Create a backup
make backup

# Make your changes...

# If something goes wrong, restore
make restore
```

### Proxy Configuration

```bash
# Create or edit proxies.txt with one proxy per line
nano proxies.txt

# Load the proxies
make load-proxies

# Verify they're loaded
make status
```

### Fresh Install

```bash
# Remove all data and reinstall from scratch
make install-fresh

# Setup the application again
make setup
```

## Backup Management

Backups are stored in the `backups/` directory with timestamps:

```
backups/
  backup-20231122-143022/
    downloader_config.json
    data/
    proxies.txt
  backup-20231123-091505/
    ...
```

Use `make restore` to interactively select and restore from any backup.

## Dependencies

The Makefile expects:
- Python 3.8+
- Standard Unix tools (find, grep, etc.)
- Virtual environment support

Optional but recommended:
- ffmpeg (for media processing)
- ruff or black (for code formatting)
- git (for version control)

## Troubleshooting

### "Virtual environment not found"

Run `make install` first to create the virtual environment.

### "No backups found"

Create a backup first with `make backup`.

### Permission Issues

The Makefile may need execute permissions on shell scripts:

```bash
chmod +x run.sh
```
