# Python YouTube Downloader

YouTubeDownloader is a Python script for downloading YouTube videos, playlists, and videos from channels with specified qualities. It features a user-friendly console interface with multi-select options for playlists, comprehensive download summaries, and disk space checks before downloads.

## Installation

1. Ensure Python is installed on your system.
2. Install required packages:

```bash
pip install pytube tqdm PyInquirer colorama
```

## Running The Script
```bash
python3 main.py
```

## Configuration
The script uses config.json for storing user preferences such as download path and default video quality. If the configuration file does not exist, the script will prompt for necessary information and offer to save it for future sessions.

```json
{
  "quality": "1080p",
  "download_path": "./downloads",
  "auto_download": [
    "https://www.youtube.com/playlist?list=PLAYLIST_ID",
    "https://www.youtube.com/channel/CHANNEL_ID"
  ],
  "notification": "email" // or "slack"
}
```

The `"quality": "1080p"` sets the default video quality to 1080p for downloads. You can adjust this to other supported resolutions like 720p, 480p, etc, depending on your needs.

The `"download_path": "./downloads"` specifies the default path where the downloaded videos will be saved. You can change this to any valid directory path on your system.

## Features

- Download individual videos or entire playlists with specified quality.
- Select and download videos from YouTube channels.
- Check for sufficient disk space before downloading.
- Console interface with progress bars and multi-select options.
- Logging of key events with timestamps.
- Can override the config with new defaults when required.
- The script now includes a try-except block around the disk space check and configuration file operations to catch and handle errors gracefully.
- Automatic Scheduling: The script can now be scheduled to run at regular intervals, automatically downloading new content from configured playlists or channels.
- Configurable Auto-Download List: Users can specify playlists or channels in the config.json file for automatic downloading.
- Notification System: The script can now send notifications via Slack or email upon download completions or errors, enhancing the monitoring capabilities.
- Secure Credential Storage: Sensitive information for notifications is stored securely in .env files, following best practices for credential management.

### Change Log
#### v1.4.0
- Introduced a notification system with a base class and implementations for Slack and email notifications.
- Added .env support for secure storage of sensitive information like API keys and SMTP credentials.

#### v1.3.0
- Added automatic scheduling functionality to periodically check and download new videos from specified playlists or channels.
- Introduced a new auto_download configuration option to list URLs for automatic downloading.

#### v1.2.0
- Improved interactive console menus using `PyInquirer` for a more user-friendly experience.
- Added color-coded console messages with `colorama` for better visibility of success and error messages.
- Implemented disk space checks before initiating downloads to ensure sufficient storage availability.
- Introduced functionality to handle YouTube channels, allowing users to select and download content from specific playlists within a channel.
- Enhanced error handling and logging for more robust operation and troubleshooting.
- Included a safety check to run the main downloader functionality only when the script is executed directly.

#### v1.1.0
Added interactive menus using PyInquirer for improved user experience.
Implemented disk space checks before downloads to ensure sufficient storage.
Introduced color-coded console messages for better readability.
Enhanced error handling and logging for robust operation.

#### v1.0.0
Initial release with basic downloading capabilities.

---

### License
This project is open-source and available under the MIT License.

### Disclaimer
This tool is for personal and educational use only. Ensure compliance with YouTube's Terms of Service before downloading content.
