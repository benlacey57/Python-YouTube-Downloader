# Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- FFmpeg (for video/audio processing)

## Quick Start

### Option 1: Using the run script (Recommended)

The easiest way to run the application is using the provided run script:

```bash
./run.sh
```

The script will automatically:
1. Create a virtual environment if it doesn't exist
2. Install all required dependencies
3. Run the application

### Option 2: Manual Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment:**
   ```bash
   # On Linux/Mac:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Fixed Issues

### Import Errors Resolved

The following issues have been fixed:

1. **Module initialization files** - Renamed `init.py` to `__init__.py` in:
   - `database/`
   - `notifiers/`
   - `models/`
   - `ui/`

2. **Notifiers module** - Fixed import of `SlackNotifier` from `slack.py` (not `slack_notifier.py`)

3. **UI module** - Fixed import of `StatsViewer` (was incorrectly referencing non-existent `StatsDisplay`)

4. **Optional MySQL dependency** - Made MySQL connector optional, allowing the app to run with SQLite by default

5. **Queue model** - Added missing `started_at` and `status` fields to the Queue dataclass

## Dependencies

Core dependencies:
- yt-dlp (YouTube downloader)
- rich (Terminal UI)
- requests (HTTP library)
- jinja2 (Email templates)

Optional dependencies:
- mysql-connector-python (MySQL support)
- google-auth-oauthlib (Google Drive storage)
- dropbox (Dropbox storage)
- paramiko (FTP/SFTP support)

## Troubleshooting

### "externally-managed-environment" Error

If you see this error when installing packages, it means your system Python is managed by the OS package manager. Use a virtual environment (recommended) or install packages with:

```bash
python3 -m pip install --user -r requirements.txt
```

### Missing FFmpeg

If you encounter FFmpeg-related errors, install it:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Import Errors

If you still see import errors after following the installation steps, ensure you're running the application from the project root directory and using the virtual environment's Python interpreter.
