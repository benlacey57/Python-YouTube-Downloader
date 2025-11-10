# Playlist Downloader Pro

Advanced video/audio playlist management with monitoring, statistics, and Slack notifications.

## Features

- 📥 Download entire playlists (video or audio)
- 📊 Comprehensive statistics tracking
- 👁️ Automated playlist monitoring
- 🔔 Size threshold alerts
- 💬 Slack notifications
- 🌐 Proxy support with validation
- 📝 Customizable filename templates
- ⚡ Parallel downloads
- 🗄️ SQLite database for persistence
- 🔄 Resume incomplete downloads

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install FFmpeg (required for audio conversion)
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
choco install ffmpeg
Usage
python main.py
Project Structure
playlist_downloader/
├── main.py                    # Application entry point
├── enums.py                   # Enumerations
├── models/                    # Database models
│   ├── channel.py
│   ├── queue.py
│   ├── download_item.py
│   ├── daily_stats.py
│   └── download_alert.py
├── managers/                  # Business logic
│   ├── database_manager.py
│   ├── config_manager.py
│   ├── stats_manager.py
│   ├── queue_manager.py
│   ├── monitor_manager.py
│   └── proxy_manager.py
├── downloaders/               # Download logic
│   └── playlist_downloader.py
├── utils/                     # Utilities
│   ├── file_renamer.py
│   └── oauth_handler.py
├── notifiers/                 # Notifications
│   └── slack_notifier.py
└── ui/                        # User interface
    ├── menu.py
    ├── settings_menu.py
    ├── monitoring_menu.py
    ├── stats_display.py
    └── progress_display.py
Configuration
Proxies
Create either proxies.txt or proxies.csv:
proxies.txt:
http://proxy1.example.com:8080
socks5://127.0.0.1:1080
proxies.csv:
http://proxy1.example.com:8080,US Proxy
socks5://127.0.0.1:1080,Local SOCKS
Authentication
Use cookies.txt for YouTube authentication:
Install browser extension (Chrome: "Get cookies.txt LOCALLY")
Export cookies whilst logged in to YouTube
Configure in Settings menu
Slack Notifications
Create Slack app at https://api.slack.com/apps
Enable Incoming Webhooks
Copy webhook URL
Configure in Settings menu
Database
All data is stored in playlist_downloader.db (SQLite):
Channels and monitoring settings
Download queues and items
Daily statistics
Alert thresholds
License
MIT License
Perfect! The complete application is now ready. Here's what we've built:

## Summary of Architecture

✅ **Modular Structure**: One class per file, one responsibility per method
✅ **SQLite Database**: Relational data with proper foreign keys
✅ **Download Size Alerts**: Configurable thresholds (250MB, 1GB, 5GB, 10GB)
✅ **Proxy Validation**: Test and remove dead proxies
✅ **Clean Progress Display**: Single progress bar, no yt-dlp clutter
✅ **Channel-Based Monitoring**: Auto-discover channels from playlists
✅ **Graceful Error Handling**: Proper try-catch for CSV parsing and all operations
✅ **Statistics Tracking**: Daily stats with empty date handling
✅ **Slack Notifications**: Queue completion, failures, size alerts
✅ **File Size Tracking**: Recorded on download completion

To run the application:

```bash
pip install -r requirements.txt
python main.py
