#!/usr/bin/env python3
"""Google Colab setup and helper functions"""
import os
import sys
from pathlib import Path
from datetime import datetime


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
        print("⚠️  Not running in Google Colab")
        return False
    
    print("🌟 Setting up YouTube Playlist Downloader for Google Colab...")
    
    # Mount Google Drive
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        print("✓ Google Drive mounted")
    except Exception as e:
        print(f"⚠️  Could not mount Google Drive: {e}")
    
    # Set working directory in Google Drive
    work_dir = '/content/drive/MyDrive/YouTube_Downloader'
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)
    print(f"✓ Working directory: {work_dir}")
    
    # Install system dependencies
    print("\n📦 Installing system dependencies...")
    
    # Install ffmpeg
    print("  • Installing ffmpeg...")
    os.system('apt-get update -qq > /dev/null 2>&1')
    os.system('apt-get install -y -qq ffmpeg > /dev/null 2>&1')
    print("  ✓ ffmpeg installed")
    
    # Install Node.js (for yt-dlp JavaScript runtime)
    print("  • Installing Node.js...")
    os.system('curl -sL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1')
    os.system('apt-get install -y nodejs > /dev/null 2>&1')
    print("  ✓ Node.js installed")
    
    print("\n✅ Colab environment ready!")
    print(f"📂 All files will be saved to: {work_dir}")
    print(f"💾 Database: {work_dir}/downloads.db")
    print(f"📥 Downloads: {work_dir}/downloads/")
    
    return True


def colab_download_queue(playlist_url, format_type='audio', file_format='mp3', 
                         quality=None, batch_size=None):
    """
    Create and prepare a download queue for Colab (no interactive menu)
    
    Args:
        playlist_url: YouTube playlist URL
        format_type: 'audio' or 'video'
        file_format: Output format (mp3, mp4, etc.)
        quality: Quality setting (optional, uses defaults)
        batch_size: Number of items to download (optional, downloads all)
    
    Returns:
        Queue object ready for downloading
    """
    from managers.config_manager import ConfigManager
    from managers.queue_manager import QueueManager
    from models.queue import Queue
    from models.download_item import DownloadItem
    from downloaders.playlist import PlaylistDownloader
    
    print(f"\n🔍 Fetching playlist information...")
    
    # Create downloader and fetch playlist info
    downloader = PlaylistDownloader()
    
    # Suppress yt-dlp output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        playlist_info = downloader.get_playlist_info(playlist_url)
    finally:
        sys.stdout = old_stdout
    
    if not playlist_info:
        print("❌ Failed to fetch playlist information")
        return None
    
    playlist_title = playlist_info.get('title', 'Unknown Playlist')
    video_count = playlist_info.get('playlist_count', 0)
    
    print(f"✓ Found playlist: {playlist_title}")
    print(f"  Total videos: {video_count:,}")
    
    # Initialize managers
    config = ConfigManager()
    queue_manager = QueueManager()
    
    # Determine quality
    if quality is None:
        if format_type == 'audio':
            quality = config.config.default_audio_quality
        else:
            quality = config.config.default_video_quality
    
    # Create queue
    queue = Queue(
        id=None,
        playlist_url=playlist_url,
        playlist_title=playlist_title,
        format_type=format_type,
        quality=quality,
        output_dir=f"downloads/{playlist_title.replace(' ', '_')}",
        filename_template="{title}",
        file_format=file_format,
        download_order='newest_first',
        storage_provider='local',
        created_at=datetime.now().isoformat(),
        status='pending'
    )
    
    # Save queue to database
    queue_id = queue_manager.create_queue(queue)
    queue.id = queue_id
    
    print(f"\n✅ Queue created!")
    print(f"   ID: {queue_id}")
    print(f"   Format: {format_type} ({file_format})")
    print(f"   Quality: {quality}")
    
    # Add items to queue
    print(f"\n📝 Adding items to queue...")
    entries = playlist_info.get('entries', [])
    
    # Apply batch size if specified
    if batch_size and batch_size < len(entries):
        entries = entries[:batch_size]
        print(f"   Using batch mode: {batch_size} of {video_count} items")
    
    added_count = 0
    for entry in entries:
        if not entry:
            continue
        
        item = DownloadItem(
            id=None,
            queue_id=queue_id,
            url=entry.get('url', ''),
            title=entry.get('title', 'Unknown'),
            video_id=entry.get('id'),
            uploader=entry.get('uploader'),
            upload_date=entry.get('upload_date'),
            file_path=None,
            file_size_bytes=None,
            file_hash=None,
            status='pending',
            error=None,
            download_started_at=None,
            download_completed_at=None,
            download_duration_seconds=None
        )
        
        queue_manager.add_item(item)
        added_count += 1
    
    print(f"✓ Added {added_count:,} items to queue")
    
    return queue


def colab_start_download(queue):
    """
    Start downloading a queue (non-interactive)
    
    Args:
        queue: Queue object from colab_download_queue()
    """
    from managers.queue_manager import QueueManager
    from downloaders.playlist import PlaylistDownloader
    
    if not queue:
        print("❌ No queue provided")
        return
    
    print(f"\n🚀 Starting download: {queue.playlist_title}")
    print(f"   Format: {queue.format_type} ({queue.file_format})")
    print(f"   Output: {queue.output_dir}")
    print()
    
    # Initialize managers and downloader
    queue_manager = QueueManager()
    downloader = PlaylistDownloader()
    
    # Start download
    try:
        downloader.download_queue(queue, queue_manager)
        print("\n✅ Download complete!")
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        import traceback
        traceback.print_exc()


def colab_list_downloads():
    """List all downloaded files"""
    import subprocess
    
    print("\n📂 Downloaded Files:")
    print("=" * 70)
    
    result = subprocess.run(
        ['find', 'downloads/', '-type', 'f', '-not', '-path', '*/.*'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout:
        files = result.stdout.strip().split('\n')
        total_size = 0
        
        for file_path in files:
            if file_path:
                size = Path(file_path).stat().st_size
                size_mb = size / (1024 * 1024)
                total_size += size
                print(f"  {file_path} ({size_mb:.2f} MB)")
        
        print("=" * 70)
        print(f"Total: {len(files)} files, {total_size / (1024 * 1024):.2f} MB")
    else:
        print("  No files found")


def colab_backup_to_drive():
    """Backup database to Google Drive"""
    import shutil
    
    if not is_colab():
        print("⚠️  Not running in Colab")
        return
    
    backup_dir = '/content/drive/MyDrive/YouTube_Downloader_Backups'
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    # Backup database
    db_file = 'downloads.db'
    if Path(db_file).exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{backup_dir}/downloads_{timestamp}.db"
        shutil.copy(db_file, backup_file)
        print(f"✓ Database backed up to: {backup_file}")
    else:
        print("⚠️  No database file found")
    
    # Backup config
    config_file = 'config.json'
    if Path(config_file).exists():
        backup_file = f"{backup_dir}/config.json"
        shutil.copy(config_file, backup_file)
        print(f"✓ Config backed up to: {backup_file}")


def colab_quick_download(playlist_url, format_type='audio', file_format='mp3'):
    """
    One-command download (creates queue and starts download)
    
    Args:
        playlist_url: YouTube playlist URL
        format_type: 'audio' or 'video'
        file_format: Output format (mp3, mp4, etc.)
    """
    print("🎵 YouTube Playlist Downloader - Colab Mode")
    print("=" * 70)
    
    # Create queue
    queue = colab_download_queue(playlist_url, format_type, file_format)
    
    if not queue:
        return
    
    # Start download
    colab_start_download(queue)
    
    # Show results
    colab_list_downloads()
    
    # Offer backup
    response = input("\n💾 Backup database to Google Drive? [y/N]: ").strip().lower()
    if response in ['y', 'yes']:
        colab_backup_to_drive()
    
    print("\n✅ All done!")


# Helper function for displaying usage
def colab_help():
    """Display usage instructions for Colab"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║           YouTube Playlist Downloader - Google Colab Mode                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

📖 Quick Start:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Setup environment (run once):
   >>> from colab_setup import setup_colab_environment
   >>> setup_colab_environment()

2️⃣  Quick download (easiest):
   >>> from colab_setup import colab_quick_download
   >>> colab_quick_download("https://youtube.com/playlist?list=...")

3️⃣  Advanced usage (more control):
   >>> from colab_setup import colab_download_queue, colab_start_download
   >>> 
   >>> # Create queue
   >>> queue = colab_download_queue(
   ...     "https://youtube.com/playlist?list=...",
   ...     format_type='audio',
   ...     file_format='mp3',
   ...     batch_size=50  # Download first 50 items
   ... )
   >>> 
   >>> # Start download
   >>> colab_start_download(queue)

📋 Available Functions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • setup_colab_environment()          - Setup Colab environment
  • colab_quick_download(url, ...)     - One-command download
  • colab_download_queue(url, ...)     - Create download queue
  • colab_start_download(queue)        - Start downloading queue
  • colab_list_downloads()             - List downloaded files
  • colab_backup_to_drive()            - Backup database to Drive
  • colab_help()                       - Show this help

💡 Tips:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • All files saved to Google Drive (persistent across sessions)
  • Database auto-commits (safe from session timeouts)
  • Use batch_size for large playlists
  • Backup database regularly with colab_backup_to_drive()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    colab_help()
