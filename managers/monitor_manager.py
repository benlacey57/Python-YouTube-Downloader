"""Channel monitoring management"""
import sqlite3
import threading
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from rich.console import Console

from models.channel import Channel

console = Console()


class MonitorManager:
    """Manages channel monitoring"""
    
    def __init__(self, db_path: str = "downloads.db"):
        self.db_path = Path(db_path)
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._init_database()
    
    def _init_database(self):
        """Initialize monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    is_monitored BOOLEAN DEFAULT 1,
                    check_interval_minutes INTEGER DEFAULT 60,
                    last_checked TEXT,
                    format_type TEXT DEFAULT 'video',
                    quality TEXT DEFAULT '720p',
                    output_dir TEXT NOT NULL,
                    filename_template TEXT,
                    download_order TEXT DEFAULT 'original',
                    enabled BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS check_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    checked_at TEXT NOT NULL,
                    new_videos_found INTEGER DEFAULT 0,
                    status TEXT,
                    error TEXT,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)
            
            conn.commit()
    
    def add_channel(self, channel: Channel) -> Channel:
        """Add a channel to monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO channels (
                        url, title, is_monitored, check_interval_minutes,
                        format_type, quality, output_dir, filename_template,
                        download_order, enabled, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    channel.url,
                    channel.title,
                    channel.is_monitored,
                    channel.check_interval_minutes,
                    channel.format_type,
                    channel.quality,
                    channel.output_dir,
                    channel.filename_template,
                    channel.download_order,
                    channel.enabled,
                    datetime.now().isoformat()
                ))
                
                channel.id = cursor.lastrowid
                conn.commit()
                
                return channel
            
            except sqlite3.IntegrityError:
                console.print(f"[yellow]Channel already exists: {channel.url}[/yellow]")
                # Get existing channel
                cursor.execute("SELECT * FROM channels WHERE url = ?", (channel.url,))
                row = cursor.fetchone()
                if row:
                    return Channel.from_row(row)
                return channel
    
    def update_channel(self, channel: Channel):
        """Update channel information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE channels SET
                    title = ?,
                    is_monitored = ?,
                    check_interval_minutes = ?,
                    last_checked = ?,
                    format_type = ?,
                    quality = ?,
                    output_dir = ?,
                    filename_template = ?,
                    download_order = ?,
                    enabled = ?
                WHERE id = ?
            """, (
                channel.title,
                channel.is_monitored,
                channel.check_interval_minutes,
                channel.last_checked,
                channel.format_type,
                channel.quality,
                channel.output_dir,
                channel.filename_template,
                channel.download_order,
                channel.enabled,
                channel.id
            ))
            
            conn.commit()
    
    def get_channel(self, channel_id: int) -> Optional[Channel]:
        """Get channel by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
            row = cursor.fetchone()
            
            if row:
                return Channel.from_row(row)
            return None
    
    def get_channel_by_url(self, url: str) -> Optional[Channel]:
        """Get channel by URL"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels WHERE url = ?", (url,))
            row = cursor.fetchone()
            
            if row:
                return Channel.from_row(row)
            return None
    
    def get_all_channels(self) -> List[Channel]:
        """Get all channels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            return [Channel.from_row(row) for row in rows]
    
    def get_monitored_channels(self) -> List[Channel]:
        """Get all monitored and enabled channels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM channels 
                WHERE is_monitored = 1 AND enabled = 1
                ORDER BY last_checked ASC NULLS FIRST
            """)
            rows = cursor.fetchall()
            
            return [Channel.from_row(row) for row in rows]
    
    def delete_channel(self, channel_id: int):
        """Delete a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete check history
            cursor.execute("DELETE FROM check_history WHERE channel_id = ?", (channel_id,))
            
            # Delete channel
            cursor.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
            
            conn.commit()
    
    def record_check(self, channel_id: int, new_videos: int, status: str, error: str = None):
        """Record a monitoring check"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO check_history (
                    channel_id, checked_at, new_videos_found, status, error
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                channel_id,
                datetime.now().isoformat(),
                new_videos,
                status,
                error
            ))
            
            conn.commit()
    
    def get_check_history(self, channel_id: int, limit: int = 10) -> List[tuple]:
        """Get check history for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT checked_at, new_videos_found, status, error
                FROM check_history
                WHERE channel_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
            """, (channel_id, limit))
            
            return cursor.fetchall()
    
    def start_monitoring(self, downloader, queue_manager, config_manager, slack_notifier):
        """Start the monitoring loop"""
        if self.is_running:
            console.print("[yellow]Monitoring is already running[/yellow]")
            return
        
        self.is_running = True
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(downloader, queue_manager, config_manager, slack_notifier),
            daemon=True
        )
        self.monitor_thread.start()
        
        console.print("[green]✓ Monitoring started[/green]")
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        if not self.is_running:
            console.print("[yellow]Monitoring is not running[/yellow]")
            return
        
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        console.print("[yellow]Monitoring stopped[/yellow]")

    def _monitor_loop(self, downloader, queue_manager, config_manager, slack_notifier):
        """Main monitoring loop"""
        console.print("[cyan]Monitoring loop started[/cyan]")
        
        while self.is_running:
            try:
                channels = self.get_monitored_channels()
                
                for channel in channels:
                    if not self.is_running:
                        break
                    
                    # Check if it's time to check this channel
                    if self._should_check_channel(channel):
                        console.print(f"[cyan]Checking channel: {channel.title}[/cyan]")
                        
                        try:
                            # Check for new videos
                            new_videos = self._check_channel_for_new_videos(
                                channel, downloader, queue_manager, config_manager
                            )
                            
                            # Update last checked time
                            channel.last_checked = datetime.now().isoformat()
                            self.update_channel(channel)
                            
                            # Record the check
                            self.record_check(channel.id, new_videos, "success")
                            
                            if new_videos > 0:
                                console.print(f"[green]✓ Found {new_videos} new videos in {channel.title}[/green]")
                                
                                # Send Slack notification
                                if slack_notifier and slack_notifier.is_configured():
                                    slack_notifier.notify_new_videos(channel.title, new_videos)
                            else:
                                console.print(f"[dim]No new videos in {channel.title}[/dim]")
                        
                        except Exception as e:
                            error_msg = str(e)
                            console.print(f"[red]Error checking {channel.title}: {error_msg}[/red]")
                            self.record_check(channel.id, 0, "error", error_msg)
                
                # Sleep for a minute before next iteration
                time.sleep(60)
            
            except Exception as e:
                console.print(f"[red]Monitor loop error: {e}[/red]")
                time.sleep(60)
        
        console.print("[cyan]Monitoring loop stopped[/cyan]")
    
    def _should_check_channel(self, channel: Channel) -> bool:
        """Determine if a channel should be checked now"""
        if not channel.last_checked:
            return True
        
        try:
            last_checked = datetime.fromisoformat(channel.last_checked)
            time_since_check = datetime.now() - last_checked
            check_interval = timedelta(minutes=channel.check_interval_minutes)
            
            return time_since_check >= check_interval
        except:
            return True
    
    def _check_channel_for_new_videos(self, channel: Channel, downloader, 
                                     queue_manager, config_manager) -> int:
        """Check channel for new videos and queue them"""
        # This is a simplified version - you may need to implement
        # tracking of already downloaded videos
        
        # Get playlist info
        playlist_info = downloader.get_playlist_info(channel.url)
        
        if not playlist_info:
            return 0
        
        entries = playlist_info.get('entries', [])
        
        if not entries:
            return 0
        
        # Get existing queues for this channel
        existing_queues = [
            q for q in queue_manager.get_all_queues()
            if q.playlist_url == channel.url
        ]
        
        # Get all video IDs we already have
        existing_video_ids = set()
        for queue in existing_queues:
            items = queue_manager.get_queue_items(queue.id)
            existing_video_ids.update(
                item.video_id for item in items if item.video_id
            )
        
        # Find new videos
        new_entries = [
            entry for entry in entries
            if entry and entry.get('id') not in existing_video_ids
        ]
        
        if not new_entries:
            return 0
        
        # Create a new queue for new videos
        from models.queue import Queue
        from models.download_item import DownloadItem
        from enums import DownloadStatus
        
        playlist_title = playlist_info.get('title', 'Unknown Playlist')
        
        queue = Queue(
            id=None,
            playlist_url=channel.url,
            playlist_title=f"{playlist_title} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            format_type=channel.format_type,
            quality=channel.quality,
            output_dir=channel.output_dir,
            download_order=channel.download_order,
            filename_template=channel.filename_template,
            storage_provider="local"
        )
        
        queue = queue_manager.create_queue(queue)
        
        # Add new videos to queue
        for entry in new_entries:
            item = DownloadItem(
                id=None,
                queue_id=queue.id,
                url=entry.get('url', ''),
                title=entry.get('title', 'Unknown'),
                status=DownloadStatus.PENDING.value,
                uploader=entry.get('uploader'),
                upload_date=entry.get('upload_date'),
                video_id=entry.get('id')
            )
            
            queue_manager.add_item_to_queue(item)
        
        # Start download if auto-download is enabled
        # For now, just queue them - you can add auto-download logic later
        
        return len(new_entries)
    
    def check_all_channels(self, downloader, queue_manager, config_manager, slack_notifier):
        """Manually check all monitored channels"""
        channels = self.get_monitored_channels()
        
        if not channels:
            console.print("[yellow]No channels to monitor[/yellow]")
            return
        
        console.print(f"[cyan]Checking {len(channels)} channels...[/cyan]")
        
        total_new_videos = 0
        
        for channel in channels:
            try:
                console.print(f"\n[cyan]Checking: {channel.title}[/cyan]")
                
                new_videos = self._check_channel_for_new_videos(
                    channel, downloader, queue_manager, config_manager
                )
                
                # Update last checked time
                channel.last_checked = datetime.now().isoformat()
                self.update_channel(channel)
                
                # Record the check
                self.record_check(channel.id, new_videos, "success")
                
                if new_videos > 0:
                    console.print(f"[green]✓ Found {new_videos} new videos[/green]")
                    total_new_videos += new_videos
                else:
                    console.print(f"[dim]No new videos[/dim]")
            
            except Exception as e:
                error_msg = str(e)
                console.print(f"[red]Error: {error_msg}[/red]")
                self.record_check(channel.id, 0, "error", error_msg)
        
        console.print(f"\n[green]✓ Check completed: {total_new_videos} new videos found[/green]")
        
        if total_new_videos > 0 and slack_notifier and slack_notifier.is_configured():
            slack_notifier.notify_monitoring_summary(len(channels), total_new_videos)
