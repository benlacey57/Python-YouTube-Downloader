"""Playlist monitoring management"""
import threading
import time
from typing import List, Optional
from datetime import datetime
from rich.console import Console

from models.channel import Channel
from managers.database_manager import DatabaseManager

console = Console()


class MonitorManager:
    """Manages playlist monitoring"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None

    def add_channel(self, channel: Channel) -> int:
        """Add a channel to monitoring"""
        # Check if channel already exists
        existing = self.db.fetch_one(
            "SELECT id FROM channels WHERE url = ?",
            (channel.url,)
        )
        
        if existing:
            # Update existing channel
            self.db.execute_query(
                """UPDATE channels SET 
                   title = ?, is_monitored = ?, check_interval_minutes = ?,
                   last_checked = ?, last_video_date = ?, enabled = ?,
                   format_type = ?, quality = ?, output_dir = ?,
                   filename_template = ?, download_order = ?, updated_at = ?
                   WHERE id = ?""",
                channel.prepare_for_update()
            )
            return existing[0]
        else:
            # Insert new channel
            self.db.execute_query(
                """INSERT INTO channels 
                   (url, title, is_monitored, check_interval_minutes,
                    last_checked, last_video_date, enabled, format_type,
                    quality, output_dir, filename_template, download_order,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                channel.prepare_for_insert()
            )
            return self.db.get_last_insert_id()

    def remove_channel(self, channel_id: int):
        """Remove a channel from monitoring"""
        self.db.execute_query(
            "DELETE FROM channels WHERE id = ?",
            (channel_id,)
        )

    def get_monitored_channels(self) -> List[Channel]:
        """Get all monitored channels"""
        rows = self.db.fetch_all(
            "SELECT * FROM channels WHERE is_monitored = 1 AND enabled = 1"
        )
        
        return [Channel.from_row(tuple(row)) for row in rows]

    def get_all_channels(self) -> List[Channel]:
        """Get all channels"""
        rows = self.db.fetch_all("SELECT * FROM channels ORDER BY created_at DESC")
        return [Channel.from_row(tuple(row)) for row in rows]

    def get_channel_by_url(self, url: str) -> Optional[Channel]:
        """Get a channel by URL"""
        row = self.db.fetch_one(
            "SELECT * FROM channels WHERE url = ?",
            (url,)
        )
        
        if row:
            return Channel.from_row(tuple(row))
        return None

    def update_channel(self, channel: Channel):
        """Update a channel"""
        self.db.execute_query(
            """UPDATE channels SET 
               title = ?, is_monitored = ?, check_interval_minutes = ?,
               last_checked = ?, last_video_date = ?, enabled = ?,
               format_type = ?, quality = ?, output_dir = ?,
               filename_template = ?, download_order = ?, updated_at = ?
               WHERE id = ?""",
            channel.prepare_for_update()
        )

    def start_monitoring(self, check_callback):
        """Start monitoring thread"""
        if self.is_running:
            return

        self.is_running = True

        def monitor_loop():
            while self.is_running:
                try:
                    channels = self.get_monitored_channels()
                    
                    if channels:
                        check_callback(channels)
                        
                        # Sleep for shortest interval
                        min_interval = min(c.check_interval_minutes for c in channels)
                        time.sleep(min_interval * 60)
                    else:
                        time.sleep(300)  # 5 minutes default

                except Exception as e:
                    console.print(f"[red]Monitor error: {e}[/red]")
                    time.sleep(60)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        console.print("[green]✓ Monitoring started[/green]")

    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        console.print("[yellow]Monitoring stopped[/yellow]")
