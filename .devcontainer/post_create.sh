#!/bin/bash
#
# This script runs after the container is created but before VS Code connects.
# It sets up the virtual environment (venv) and runs the application installer.

echo "--- 1. Setting up Python virtual environment (venv) ---"
# Create the venv
python3 -m venv venv
# Activate the venv environment for the current shell session
source venv/bin/activate
echo "Virtual environment created and activated."

echo "--- 2. Installing Python dependencies ---"
# Install all required packages into the new venv
if [ -f "requirements.txt" ]; then
    # Use pip from the venv
    ./venv/bin/pip install --no-cache-dir -r requirements.txt
    echo "Dependencies installed from requirements.txt."
else
    # Install core dependencies if requirements.txt is missing
    echo "Warning: requirements.txt not found. Installing yt-dlp and rich directly..."
    ./venv/bin/pip install --no-cache-dir yt-dlp rich
fi

# --- 3. Run the Application's Custom Installer ---
echo "--- Running custom application setup (install.py) ---"
if [ -f "install.py" ]; then
    # Use the installed python executable inside the venv
    ./venv/bin/python install.py --no-wizard
else
    echo "Error: install.py not found. Initial setup skipped."
fi

echo "--- Post Create script finished successfully ---"
