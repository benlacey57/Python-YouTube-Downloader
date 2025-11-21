# Cloud Deployment & Google Drive Integration Guide

## Overview
This guide covers running the YouTube Playlist Downloader in cloud environments, ensuring database persistence, and integrating with Google Drive.

---

## 1. Database Auto-Commit for Cloud Environments

### Current Implementation ✅

The SQLite connection **already uses auto-commit** via context managers:

```python
@contextmanager
def get_connection(self):
    conn = sqlite3.connect(self.db_path)
    try:
        yield conn
        conn.commit()  # ✅ Auto-commit on success
    except Exception:
        conn.rollback()  # ✅ Auto-rollback on error
        raise
    finally:
        conn.close()
```

**This means:**
- ✅ Every database operation commits immediately
- ✅ Safe for cloud environments
- ✅ No data loss if process terminates
- ✅ Works in Google Colab, AWS, Azure, etc.

### SQLite vs MySQL for Cloud

**SQLite (Current):**
- ✅ File-based, portable
- ✅ Zero configuration
- ✅ Works perfectly in Colab
- ✅ Auto-commits every operation
- ❌ Single writer at a time
- ❌ File must be uploaded/downloaded

**MySQL (Alternative):**
- ✅ Multi-user support
- ✅ Remote access
- ✅ Better for distributed systems
- ❌ Requires server setup
- ❌ More complex configuration

**Recommendation:**
- **Google Colab / Single User:** Use SQLite ✅
- **Multi-user / Production:** Use MySQL
- **Hybrid:** Use both (already supported!)

---

## 2. Google Drive Integration

### Setup Google Drive Storage

#### Step 1: Enable Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Drive API"
4. Create OAuth 2.0 credentials
5. Download `credentials.json`

#### Step 2: Install Dependencies

Already in `requirements.txt`:
```
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.108.0
```

#### Step 3: Configure in Application

**Option A: Using Setup Wizard**
```
Settings > Storage Management > Add Storage Provider

Provider Name: Google Drive
Provider Type: google_drive
Root Folder ID: [leave blank for root]
```

**Option B: Manual Configuration**

Edit `config.json`:
```json
{
  "storage_providers": {
    "gdrive": {
      "type": "google_drive",
      "credentials_file": "credentials.json",
      "token_file": "token.json",
      "root_folder_id": null,
      "upload_chunk_size": 10485760
    }
  }
}
```

#### Step 4: First-Time Authentication

Run the application:
```bash
./run.sh
```

On first use, it will:
1. Open browser for Google OAuth
2. Ask for Drive access permission
3. Save token to `token.json`
4. Future runs won't need browser

**For Google Colab:**
```python
# Will use Colab's auth flow
from google.colab import auth
auth.authenticate_user()
```

### Using Google Drive Storage

**When creating a queue:**
```
Step 6: Storage Options
Storage provider [local/gdrive] (local): gdrive

✓ Files will be uploaded to Google Drive after download
```

**Workflow:**
1. Download to local temp directory
2. Upload to Google Drive
3. Optionally delete local copy
4. Track in database with Drive file ID

---

## 3. Google Colab Compatibility

### The Loop Issue

**Problem:**
Google Colab notebooks can't run interactive terminal loops (like menus) because they don't have true TTY support.

**Solution:**
Create a Colab-specific interface using IPython widgets instead of Rich terminal UI.

### Colab Setup Script

Create `colab_setup.py`:

```python
"""Google Colab setup and helpers"""
import os
import sys
from pathlib import Path

def is_colab():
    """Check if running in Google Colab"""
    try:
        import google.colab
        return True
    except ImportError:
        return False

def setup_colab_environment():
    """Setup environment for Google Colab"""
    if not is_colab():
        return False
    
    print("🌟 Setting up for Google Colab...")
    
    # Mount Google Drive
    from google.colab import drive
    drive.mount('/content/drive')
    
    # Set working directory
    work_dir = '/content/drive/MyDrive/YouTube_Downloader'
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)
    
    # Install ffmpeg
    !apt-get update -qq
    !apt-get install -y -qq ffmpeg
    
    # Install Node.js
    !curl -sL https://deb.nodesource.com/setup_18.x | bash -
    !apt-get install -y nodejs
    
    print("✅ Colab environment ready!")
    print(f"📂 Working directory: {work_dir}")
    
    return True

def colab_download_queue(playlist_url, format_type='audio', file_format='mp3'):
    """Simplified download for Colab (no interactive menu)"""
    from managers.config_manager import ConfigManager
    from managers.queue_manager import QueueManager
    from models.queue import Queue
    from downloaders.playlist import PlaylistDownloader
    from datetime import datetime
    
    # Create queue
    downloader = PlaylistDownloader()
    playlist_info = downloader.get_playlist_info(playlist_url)
    
    if not playlist_info:
        print("❌ Failed to fetch playlist")
        return None
    
    config = ConfigManager()
    queue_manager = QueueManager()
    
    queue = Queue(
        id=None,
        playlist_url=playlist_url,
        playlist_title=playlist_info['title'],
        format_type=format_type,
        quality=config.config.default_audio_quality if format_type == 'audio' else '720p',
        output_dir=f"downloads/{playlist_info['title']}",
        filename_template="{title}",
        file_format=file_format,
        download_order='newest_first',
        storage_provider='local',
        created_at=datetime.now().isoformat(),
        status='pending'
    )
    
    queue_id = queue_manager.create_queue(queue)
    queue.id = queue_id
    
    print(f"✅ Queue created: {queue.playlist_title}")
    print(f"📊 Items: {playlist_info['playlist_count']}")
    
    return queue

def colab_start_download(queue):
    """Start download without interactive UI"""
    from managers.queue_manager import QueueManager
    from downloaders.playlist import PlaylistDownloader
    
    queue_manager = QueueManager()
    downloader = PlaylistDownloader()
    
    # Add items to queue
    playlist_info = downloader.get_playlist_info(queue.playlist_url)
    entries = playlist_info.get('entries', [])
    
    for entry in entries:
        if not entry:
            continue
        item = DownloadItem(
            id=None,
            queue_id=queue.id,
            url=entry.get('url', ''),
            title=entry.get('title', 'Unknown'),
            video_id=entry.get('id'),
            status='pending'
        )
        queue_manager.add_item(item)
    
    # Start download
    print("🚀 Starting download...")
    downloader.download_queue(queue, queue_manager)
    
    print("✅ Download complete!")
```

### Colab Notebook Example

```python
# === Cell 1: Setup ===
!git clone https://github.com/your-repo/YouTube_Playlist_Downloader.git
%cd YouTube_Playlist_Downloader
!pip install -q -r requirements.txt

# === Cell 2: Colab Setup ===
from colab_setup import setup_colab_environment
setup_colab_environment()

# === Cell 3: Create Queue ===
from colab_setup import colab_download_queue

queue = colab_download_queue(
    playlist_url="https://www.youtube.com/playlist?list=...",
    format_type='audio',
    file_format='mp3'
)

# === Cell 4: Start Download ===
from colab_setup import colab_start_download
colab_start_download(queue)

# === Cell 5: List Downloads ===
!ls -lh downloads/

# === Cell 6: Upload to Google Drive (Optional) ===
from google.colab import drive
drive.mount('/content/drive')

import shutil
shutil.copytree('downloads/', '/content/drive/MyDrive/Music/', dirs_exist_ok=True)
print("✅ Files copied to Google Drive!")
```

### Colab-Specific Features

**Auto-detect Colab:**
```python
# In main.py
import sys

if 'google.colab' in sys.modules:
    print("Running in Google Colab - use colab_setup.py functions")
    sys.exit(0)
```

**Non-interactive Mode:**
```python
# Add to main.py
def main():
    # Check if running in Colab
    if is_colab():
        print("⚠️  Interactive menu not available in Colab")
        print("📖 Use colab_setup.py functions instead")
        print("Example: colab_download_queue(url, format_type, file_format)")
        return
    
    # Regular interactive menu
    menu = Menu()
    menu.show()
```

---

## 4. Cloud Deployment Strategies

### A. Google Colab

**Pros:**
- ✅ Free GPU/TPU
- ✅ Pre-installed Python
- ✅ Google Drive integration
- ✅ No server maintenance

**Cons:**
- ❌ Session timeouts (12 hours)
- ❌ No background execution
- ❌ Interactive UI limitations

**Best For:**
- One-time downloads
- Testing
- Personal use

**Setup:**
```python
# Install in Colab
!git clone <repo>
%cd YouTube_Playlist_Downloader
!pip install -r requirements.txt

# Use non-interactive functions
from colab_setup import *
```

### B. AWS EC2 / Google Cloud VM

**Pros:**
- ✅ Persistent
- ✅ Full control
- ✅ Can run 24/7
- ✅ Interactive terminal

**Cons:**
- ❌ Costs money
- ❌ Requires setup
- ❌ Maintenance needed

**Best For:**
- Production use
- Automated downloads
- Channel monitoring

**Setup:**
```bash
# Install on VM
git clone <repo>
cd YouTube_Playlist_Downloader
./install.py

# Run with screen/tmux
screen -S downloader
./run.sh

# Detach: Ctrl+A, D
# Reattach: screen -r downloader
```

### C. Docker Container

**Pros:**
- ✅ Portable
- ✅ Consistent environment
- ✅ Easy deployment
- ✅ Can run anywhere

**Create `Dockerfile`:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run application
CMD ["python", "main.py"]
```

**Run:**
```bash
docker build -t youtube-downloader .
docker run -v $(pwd)/downloads:/app/downloads youtube-downloader
```

---

## 5. Database Persistence Best Practices

### For SQLite in Cloud

**1. Regular Backups:**
```bash
# Backup database
cp downloads.db downloads.db.backup

# Or use SQLite backup
sqlite3 downloads.db ".backup downloads.db.backup"
```

**2. Sync to Cloud Storage:**
```python
# Auto-sync database to Google Drive after each queue
import shutil
shutil.copy('downloads.db', '/content/drive/MyDrive/backups/downloads.db')
```

**3. Use WAL Mode:**
```python
# In SQLiteConnection.__init__
conn = sqlite3.connect(self.db_path)
conn.execute('PRAGMA journal_mode=WAL')
```

### For MySQL in Cloud

**Setup Remote MySQL:**
```python
# config.json
{
  "database": {
    "type": "mysql",
    "host": "your-mysql-host.com",
    "port": 3306,
    "database": "youtube_downloader",
    "user": "your_user",
    "password": "your_password"
  }
}
```

**Advantages:**
- ✅ No file syncing needed
- ✅ Multi-instance support
- ✅ Better for production
- ✅ Automatic persistence

---

## 6. Troubleshooting

### Issue: Database not committing in Colab
**Solution:** Already fixed with context managers, commits are automatic

### Issue: Google Drive authentication fails in Colab
**Solution:** Use `google.colab.auth.authenticate_user()`

### Issue: Interactive menu hangs in Colab
**Solution:** Use `colab_setup.py` functions instead of interactive menu

### Issue: Session timeout loses progress
**Solution:** 
- Use smaller batches
- Database auto-commits protect progress
- Resume from last completed item

### Issue: SQLite database locked
**Solution:**
- Enable WAL mode
- Don't run multiple instances
- Or switch to MySQL

---

## 7. Quick Start Guides

### Colab Quick Start

```python
# 1. Setup
!git clone <repo> && cd YouTube_Playlist_Downloader
!pip install -r requirements.txt
from colab_setup import *
setup_colab_environment()

# 2. Download
queue = colab_download_queue("https://youtube.com/playlist?list=...")
colab_start_download(queue)

# 3. Backup
!cp downloads.db /content/drive/MyDrive/backups/
```

### AWS/GCP Quick Start

```bash
# 1. Setup
git clone <repo>
cd YouTube_Playlist_Downloader
./install.py

# 2. Run
screen -S downloader
./run.sh

# 3. Detach
# Ctrl+A, D
```

### Docker Quick Start

```bash
# 1. Build
docker build -t youtube-downloader .

# 2. Run
docker run -v $(pwd)/downloads:/app/downloads \
           -v $(pwd)/downloads.db:/app/downloads.db \
           youtube-downloader
```

---

## Summary

**Database:**
- ✅ SQLite auto-commits - safe for cloud
- ✅ No changes needed
- 🔄 MySQL optional for multi-user

**Google Drive:**
- ✅ Already supported
- 📝 Needs OAuth setup
- 🔧 Configure in settings

**Colab:**
- ⚠️ Interactive menu won't work
- ✅ Use `colab_setup.py` functions
- ✅ Database persistence works
- 📂 Mount Drive for backups

Choose your deployment based on your needs! 🚀
