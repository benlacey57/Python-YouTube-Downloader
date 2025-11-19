# Utility Tools

This document describes the utility scripts available in the YouTube Playlist Downloader project.

## Installation & Setup

### install.py

**Purpose:** Interactive installation wizard that sets up the application with guided configuration.

**Usage:**
```bash
./install.py
# or
python3 install.py
# or
./venv/bin/python install.py
```

**Features:**
- ✨ Beautiful ASCII art banner
- 📦 Automatic package installation (requirements.txt + requirements-dev.txt)
- 📊 Settings preview (one section at a time)
- 🗄️ Database initialization and testing
- 🌱 Optional database seeding
- 🔧 Optional custom configuration wizard
- 📁 Automatic directory creation

**Installation Flow:**
1. System requirements check (Python version)
2. Install core dependencies
3. Install development dependencies (optional)
4. Create necessary directories (downloads/, logs/, data/)
5. Show default configuration (Download Settings, Notifications, Rate Limiting, Storage)
6. Initialize SQLite database
7. Optionally seed database with sample data
8. Optionally run setup wizard for custom configuration

**Example Output:**
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              YouTube Playlist Downloader - Installation                  ║
║                                                                           ║
║              Advanced download management system                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════
  System Requirements Check
═══════════════════════════════════════════════════════════════════════════

✓ Python version: 3.12.0

═══════════════════════════════════════════════════════════════════════════
  Installing Required Packages
═══════════════════════════════════════════════════════════════════════════

Installing core dependencies from requirements.txt...
```

---

### uninstall.py

**Purpose:** Clean uninstallation script that removes application data and configuration.

**Usage:**
```bash
./uninstall.py
# or
python3 uninstall.py

# Fresh install mode (removes venv too)
./uninstall.py --fresh
python3 uninstall.py --fresh
```

**Features:**
- ⚠️ Confirmation prompts before deletion
- 🗑️ Removes configuration files
- 🗑️ Removes database files (downloads.db, stats.db)
- 🗑️ Removes log files
- 🗑️ Cleans Python cache (__pycache__)
- 🔄 Optional: Remove virtual environment (--fresh flag)
- 🤔 Prompts about downloads directory

**What Gets Removed:**
- `config.json` - Configuration file
- `downloads.db` - Main database
- `stats.db` - Statistics database
- `logs/` - Log directory
- `data/` - Data directory (with --fresh)
- `venv/` - Virtual environment (with --fresh)
- `__pycache__/` - Python cache directories
- `downloads/` - Downloads directory (asks for confirmation)

**Example:**
```bash
$ ./uninstall.py --fresh

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            YouTube Playlist Downloader - Uninstallation                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

🔄 Fresh install mode: Will remove data directories

⚠️  WARNING: This will remove all application data!

The following will be deleted:
  • Configuration files
  • Database files (downloads.db, stats.db)
  • Log files
  • Virtual environment (if --fresh flag is used)

Are you sure you want to continue? [y/N]: y
```

---

### db_viewer.py

**Purpose:** Interactive SQLite database viewer for inspecting and browsing database contents.

**Usage:**
```bash
# Interactive mode (select database)
./db_viewer.py

# View specific database
./db_viewer.py downloads.db
./db_viewer.py stats.db
```

**Features:**
- 📊 Database file size display
- 📋 Table list with row counts and column counts
- 🔍 View last 10 entries of each table
- 💾 Formatted output with truncated long values
- ⏯️ Prompts to continue between tables
- 🎯 Interactive database selection

**Display Format:**
- Database overview (file size, table count)
- Table summary (name, row count, columns)
- Detailed view of each table:
  - Total rows
  - Column names
  - Last 10 entries with all fields

**Example Output:**
```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    SQLite Database Viewer                                ║
║              YouTube Playlist Downloader Database Inspector              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

📂 Database: downloads.db
💾 File Size: 36.00 KB
📊 Tables: 5

═══════════════════════════════════════════════════════════════════════════
  Database Overview
═══════════════════════════════════════════════════════════════════════════

TABLE SUMMARY
───────────────────────────────────────────────────────────────────────────
Table Name                       Row Count    Columns
───────────────────────────────────────────────────────────────────────────
channels                                12          7
download_items                         638         15
queues                                   3         14
daily_stats                              5         10
download_alerts                          0          8
───────────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════════
  Table: queues
═══════════════════════════════════════════════════════════════════════════

Total rows: 3
Columns: id, playlist_url, playlist_title, format_type, quality, output_dir

Showing last 3 entries:

Entry #1
────────────────────────────────────────────────────────
  id                       : 1
  playlist_url             : https://www.youtube.com/playlist?list=PLrA...
  playlist_title           : Favorites
  format_type              : audio
  quality                  : 192
  output_dir               : downloads/Favorites
  ...

Press Enter to view next table (or 'q' to quit): 
```

**Key Features:**
- **Smart value truncation:** Long values are truncated to 50 characters
- **NULL handling:** NULL values are clearly displayed
- **Pagination:** Prompts between tables to prevent overwhelming output
- **Exit anytime:** Press 'q' to quit viewing at any table
- **Multiple databases:** Automatically detects and lists available databases

---

## Shell Scripts

### run.sh

**Purpose:** Convenience script to run the application with automatic virtual environment management.

**Usage:**
```bash
./run.sh
```

**Features:**
- Automatically creates venv if it doesn't exist
- Installs dependencies if needed
- Runs the application

---

### scripts/install.sh

**Purpose:** Legacy bash installation script with system checks and venv setup.

**Usage:**
```bash
# Standard installation
bash scripts/install.sh

# Fresh installation (removes old data)
bash scripts/install.sh --fresh
```

**Features:**
- Python version check (3.8+)
- FFmpeg check (optional but recommended)
- Virtual environment creation
- Dependency installation
- Directory creation
- Calls install.py for guided setup

---

## Quick Reference

| Task | Command |
|------|---------|
| **Fresh Install** | `./install.py` or `bash scripts/install.sh` |
| **Run Application** | `./run.sh` or `python main.py` |
| **View Database** | `./db_viewer.py` |
| **Uninstall** | `./uninstall.py` |
| **Clean Reinstall** | `./uninstall.py --fresh && ./install.py` |

## Workflow Examples

### First Time Setup
```bash
# Clone repository
git clone <repo-url>
cd YouTube_Playlist_Downloader

# Run installation
./install.py

# Start using the app
./run.sh
```

### Fresh Reinstall
```bash
# Remove all data and reinstall
./uninstall.py --fresh
./install.py
```

### Database Inspection
```bash
# View database contents
./db_viewer.py

# Or view specific database
./db_viewer.py downloads.db
```

### Development Setup
```bash
# Install with dev dependencies
./install.py

# The installer automatically installs both:
# - requirements.txt (core dependencies)
# - requirements-dev.txt (dev dependencies)
```

## Notes

- All Python scripts have proper shebangs and can be executed directly
- Scripts use rich terminal output for better visual experience
- Database viewer safely handles missing databases and empty tables
- Uninstaller has safety prompts to prevent accidental data loss
- Install script provides interactive configuration or uses sensible defaults
