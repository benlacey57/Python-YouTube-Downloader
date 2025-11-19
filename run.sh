#!/bin/bash
# YouTube Playlist Downloader CLI runner

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if venv exists
if [ ! -d "$DIR/venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$DIR/venv"
    echo "Installing dependencies..."
    "$DIR/venv/bin/pip" install -r "$DIR/requirements.txt"
fi

# Run the application with the virtual environment's Python
"$DIR/venv/bin/python" "$DIR/main.py" "$@"
