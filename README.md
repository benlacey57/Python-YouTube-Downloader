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

```

## Features

- Download individual videos or entire playlists with specified quality.
- Select and download videos from YouTube channels.
- Check for sufficient disk space before downloading.
- Console interface with progress bars and multi-select options.
- Logging of key events with timestamps.
- Can override the config with new defaults when required.
- The script now includes a try-except block around the disk space check and configuration file operations to catch and handle errors gracefully.

## Disclaimer
This tool is for personal and educational use only. Ensure compliance with YouTube's Terms of Service before downloading content.
