#!/usr/bin/env python3
"""
Playlist Downloader - Advanced video/audio playlist management
Supports monitoring, OAuth, file templates, statistics, and Slack notifications
"""

import json
import os
import sys
import csv
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, date
from enum import Enum
import hashlib
import random
import shutil
import threading
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import requests

try:
    import yt_dlp
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
        DownloadColumn,
        TransferSpeedColumn,
    )
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.tree import Tree
    from rich import print as rprint
    from rich.align import Align
    from rich.columns import Columns
    import schedule
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install: pip install yt-dlp rich schedule requests")
    sys.exit(1)


console = Console()


class DownloadFormat(Enum):
    VIDEO = "video"
    AUDIO = "audio"


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadOrder(Enum):
    OLDEST_FIRST = "oldest_first"
    NEWEST_FIRST = "newest_first"
    ORIGINAL = "original"


@dataclass
class DailyStats:
    """Statistics for a single day"""
    date: str
    videos_downloaded: int = 0
    videos_queued: int = 0
    videos_failed: int = 0
    total_download_time_seconds: float = 0
    total_file_size_bytes: int = 0
    queues_created: int = 0
    queues_completed: int = 0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class StatsManager:
    """Manages daily statistics"""

    def __init__(self, stats_file: str = "download_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats: Dict[str, DailyStats] = {}
        self.load_stats()

    def load_stats(self):
        """Load statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = {
                        date_str: DailyStats.from_dict(stats_data)
                        for date_str, stats_data in data.items()
                    }
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load stats: {e}[/yellow]")

    def save_stats(self):
        """Save statistics to file"""
        try:
            # Only save dates that have activity
            data = {
                date_str: stats.to_dict()
                for date_str, stats in self.stats.items()
                if stats.videos_downloaded > 0 or stats.videos_queued > 0 or stats.videos_failed > 0
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[red]Error saving stats: {e}[/red]")

    def get_today_stats(self) -> DailyStats:
        """Get or create today's statistics"""
        today = date.today().isoformat()
        if today not in self.stats:
            self.stats[today] = DailyStats(date=today)
        return self.stats[today]

    def record_download(self, success: bool, duration_seconds: float, file_size_bytes: int = 0):
        """Record a completed download"""
        stats = self.get_today_stats()
        if success:
            stats.videos_downloaded += 1
            stats.total_download_time_seconds += duration_seconds
            stats.total_file_size_bytes += file_size_bytes
        else:
            stats.videos_failed += 1
        self.save_stats()

    def record_queue_created(self, num_items: int):
        """Record a new queue creation"""
        stats = self.get_today_stats()
        stats.queues_created += 1
        stats.videos_queued += num_items
        self.save_stats()

    def record_queue_completed(self):
        """Record a queue completion"""
        stats = self.get_today_stats()
        stats.queues_completed += 1
        self.save_stats()

    def get_date_range_stats(self, days: int = 30) -> List[DailyStats]:
        """Get statistics for the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        stats_list = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in self.stats:
                stats_list.append(self.stats[date_str])
            else:
                # Return zero stats for days with no activity
                stats_list.append(DailyStats(date=date_str))
            current_date += timedelta(days=1)

        return stats_list

    def get_summary(self, days: int = 30) -> Dict:
        """Get summary statistics for the last N days"""
        stats_list = self.get_date_range_stats(days)

        return {
            'total_downloaded': sum(s.videos_downloaded for s in stats_list),
            'total_queued': sum(s.videos_queued for s in stats_list),
            'total_failed': sum(s.videos_failed for s in stats_list),
            'total_time_seconds': sum(s.total_download_time_seconds for s in stats_list),
            'total_size_bytes': sum(s.total_file_size_bytes for s in stats_list),
            'avg_downloads_per_day': sum(s.videos_downloaded for s in stats_list) / days if days > 0 else 0,
            'queues_created': sum(s.queues_created for s in stats_list),
            'queues_completed': sum(s.queues_completed for s in stats_list),
        }


class SlackNotifier:
    """Handles Slack notifications"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def is_configured(self) -> bool:
        """Check if Slack webhook is configured"""
        return bool(self.webhook_url)

    def send_notification(self, title: str, message: str, color: str = "good"):
        """Send a notification to Slack"""
        if not self.is_configured():
            return False

        try:
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "Playlist Downloader",
                        "ts": int(time.time())
                    }
                ]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            console.print(f"[yellow]Failed to send Slack notification: {e}[/yellow]")
            return False

    def notify_queue_completed(self, queue_title: str, completed: int, failed: int, total: int, duration: str):
        """Send notification when queue completes"""
        if failed > 0:
            color = "warning"
            status = "Completed with errors"
        else:
            color = "good"
            status = "Completed successfully"

        message = (
            f"*Playlist:* {queue_title}\n"
            f"*Status:* {status}\n"
            f"*Downloaded:* {completed}/{total}\n"
            f"*Failed:* {failed}\n"
            f"*Duration:* {duration}"
        )

        return self.send_notification(f"Queue {status}", message, color)

    def notify_queue_failed(self, queue_title: str, error: str):
        """Send notification when queue fails"""
        message = (
            f"*Playlist:* {queue_title}\n"
            f"*Error:* {error}"
        )

        return self.send_notification("Queue Failed", message, "danger")

    def notify_monitoring_update(self, playlist_title: str, new_videos: int):
        """Send notification when new videos are detected"""
        message = (
            f"*Playlist:* {playlist_title}\n"
            f"*New Videos:* {new_videos}"
        )

        return self.send_notification("New Videos Detected", message, "#36a64f")

@dataclass
class DownloadItem:
    url: str
    title: str
    status: DownloadStatus
    file_path: Optional[str] = None
    error: Optional[str] = None
    file_hash: Optional[str] = None
    download_started_at: Optional[str] = None
    download_completed_at: Optional[str] = None
    download_duration_seconds: Optional[float] = None
    upload_date: Optional[str] = None
    uploader: Optional[str] = None
    video_id: Optional[str] = None
    file_size_bytes: Optional[int] = None

    def to_dict(self):
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data):
        data['status'] = DownloadStatus(data['status'])
        return cls(**data)


@dataclass
class MonitoredPlaylist:
    playlist_url: str
    playlist_title: str
    format_type: DownloadFormat
    quality: str
    output_dir: str
    last_checked: Optional[str] = None
    last_video_date: Optional[str] = None
    check_interval_minutes: int = 60
    enabled: bool = True
    filename_template: Optional[str] = None
    download_order: str = "original"

    def to_dict(self):
        data = asdict(self)
        data['format_type'] = self.format_type.value
        return data

    @classmethod
    def from_dict(cls, data):
        data['format_type'] = DownloadFormat(data['format_type'])
        return cls(**data)


@dataclass
class DownloadQueue:
    queue_id: str
    playlist_url: str
    playlist_title: str
    format_type: DownloadFormat
    quality: str
    output_dir: str
    items: List[DownloadItem]
    created_at: str
    completed_at: Optional[str] = None
    download_order: str = "original"
    filename_template: Optional[str] = None
    is_monitored: bool = False

    def to_dict(self):
        data = asdict(self)
        data['format_type'] = self.format_type.value
        data['items'] = [item.to_dict() for item in self.items]
        return data

    @classmethod
    def from_dict(cls, data):
        data['format_type'] = DownloadFormat(data['format_type'])
        data['items'] = [DownloadItem.from_dict(item) for item in data['items']]
        return cls(**data)


@dataclass
class AppConfig:
    """Application configuration"""
    cookies_file: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    oauth_expiry: Optional[str] = None
    proxies: List[str] = field(default_factory=list)
    max_workers: int = 3
    default_filename_template: str = "{index:03d} - {title}"
    monitoring_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    download_timeout_minutes: int = 120  # 2 hours default for long videos
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class FileRenamer:
    """Handles file renaming with template system"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove invalid characters and normalise filename"""
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        filename = emoji_pattern.sub('', filename)
        
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        filename = ' '.join(filename.split())
        filename = filename.strip('. ')
        
        filename = re.sub(r'[!]+', '!', filename)
        filename = re.sub(r'[?]+', '?', filename)
        filename = re.sub(r'\.{2,}', '.', filename)
        
        return filename
    
    @staticmethod
    def apply_template(template: str, item: DownloadItem, index: int = 0, 
                       playlist_title: str = "") -> str:
        """Apply filename template with placeholders"""
        placeholders = {
            'title': FileRenamer.sanitize_filename(item.title),
            'uploader': FileRenamer.sanitize_filename(item.uploader or 'Unknown'),
            'date': item.upload_date or 'Unknown',
            'index': index,
            'playlist': FileRenamer.sanitize_filename(playlist_title),
            'video_id': item.video_id or 'unknown',
        }
        
        filename = template
        for key, value in placeholders.items():
            pattern = f"{{{key}}}"
            if pattern in filename:
                filename = filename.replace(pattern, str(value))
            
            format_pattern = re.compile(r'\{' + key + r':([^}]+)\}')
            match = format_pattern.search(filename)
            if match:
                format_spec = match.group(1)
                if key == 'index':
                    formatted_value = f"{value:{format_spec}}"
                else:
                    formatted_value = str(value)
                filename = format_pattern.sub(formatted_value, filename)
        
        return FileRenamer.sanitize_filename(filename)


class OAuthHandler:
    """Handles OAuth2 authentication for YouTube"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def is_authenticated(self) -> bool:
        """Check if OAuth token is valid"""
        if not self.config.oauth_token:
            return False
        
        if self.config.oauth_expiry:
            expiry = datetime.fromisoformat(self.config.oauth_expiry)
            if datetime.now() >= expiry:
                return self.refresh_token()
        
        return True
    
    def authenticate(self) -> bool:
        """Start OAuth authentication flow"""
        console.print("\n[cyan]OAuth Authentication[/cyan]")
        console.print("\n[yellow]Note: OAuth for yt-dlp is complex and requires:[/yellow]")
        console.print("  1. Google Cloud Project with YouTube API enabled")
        console.print("  2. OAuth 2.0 Client ID credentials")
        console.print("  3. Manual token generation\n")
        
        console.print("[yellow]For now, we'll use cookies.txt as it's more reliable[/yellow]")
        console.print("[yellow]To use OAuth, you'd need to implement the full OAuth2 flow[/yellow]\n")
        
        return False
    
    def refresh_token(self) -> bool:
        """Refresh OAuth token"""
        return False
    
    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """Get authentication header for requests"""
        if self.is_authenticated():
            return {"Authorization": f"Bearer {self.config.oauth_token}"}
        return None


class ProxyManager:
    """Manages proxy rotation"""
    
    def __init__(self, proxies: List[str]):
        self.proxies = proxies if proxies else []
        self.current_index = 0
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Get random proxy"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)


class MonitorManager:
    """Manages playlist monitoring and automatic downloads"""
    
    def __init__(self, config_file: str = "monitored_playlists.json"):
        self.config_file = Path(config_file)
        self.playlists: Dict[str, MonitoredPlaylist] = {}
        self.is_running = False
        self.monitor_thread = None
        self.load_playlists()
    
    def load_playlists(self):
        """Load monitored playlists from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.playlists = {
                        url: MonitoredPlaylist.from_dict(pdata)
                        for url, pdata in data.items()
                    }
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load monitored playlists: {e}[/yellow]")
    
    def save_playlists(self):
        """Save monitored playlists to file"""
        try:
            data = {url: playlist.to_dict() for url, playlist in self.playlists.items()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[red]Error saving monitored playlists: {e}[/red]")
    
    def add_playlist(self, playlist: MonitoredPlaylist):
        """Add a playlist to monitoring"""
        self.playlists[playlist.playlist_url] = playlist
        self.save_playlists()
    
    def remove_playlist(self, playlist_url: str):
        """Remove a playlist from monitoring"""
        if playlist_url in self.playlists:
            del self.playlists[playlist_url]
            self.save_playlists()
    
    def check_for_new_videos(self, downloader, queue_manager, slack_notifier: Optional[SlackNotifier] = None) -> List[DownloadQueue]:
        """Check all monitored playlists for new videos"""
        new_queues = []
        
        for url, playlist in self.playlists.items():
            if not playlist.enabled:
                continue
            
            try:
                info = downloader.get_playlist_info(url)
                if not info:
                    continue
                
                entries = info.get('entries', [])
                if not entries:
                    continue
                
                new_videos = []
                for entry in entries:
                    if not entry:
                        continue
                    
                    upload_date = entry.get('upload_date')
                    if playlist.last_video_date and upload_date:
                        if upload_date <= playlist.last_video_date:
                            continue
                    
                    new_videos.append(entry)
                
                if new_videos:
                    items = []
                    for entry in new_videos:
                        item = DownloadItem(
                            url=entry.get('url', ''),
                            title=entry.get('title', 'Unknown'),
                            status=DownloadStatus.PENDING,
                            upload_date=entry.get('upload_date'),
                            uploader=entry.get('uploader'),
                            video_id=entry.get('id')
                        )
                        items.append(item)
                    
                    queue_id = queue_manager.create_queue(
                        playlist_url=url,
                        playlist_title=playlist.playlist_title,
                        format_type=playlist.format_type,
                        quality=playlist.quality,
                        output_dir=playlist.output_dir,
                        items=items,
                        download_order=playlist.download_order
                    )
                    
                    queue = queue_manager.get_queue(queue_id)
                    queue.is_monitored = True
                    queue.filename_template = playlist.filename_template
                    queue_manager.update_queue(queue_id, queue)
                    
                    new_queues.append(queue)
                    
                    playlist.last_checked = datetime.now().isoformat()
                    if new_videos:
                        latest_date = max(v.get('upload_date', '') for v in new_videos if v.get('upload_date'))
                        if latest_date:
                            playlist.last_video_date = latest_date
                    
                    self.save_playlists()
                    
                    console.print(f"[green]✓ Found {len(new_videos)} new videos in {playlist.playlist_title}[/green]")
                    
                    # Send Slack notification
                    if slack_notifier and slack_notifier.is_configured():
                        slack_notifier.notify_monitoring_update(playlist.playlist_title, len(new_videos))
            
            except Exception as e:
                console.print(f"[red]Error checking {playlist.playlist_title}: {e}[/red]")
        
        return new_queues
    
    def start_monitoring(self, downloader, queue_manager, slack_notifier: Optional[SlackNotifier] = None):
        """Start monitoring thread"""
        if self.is_running:
            return
        
        self.is_running = True
        
        def monitor_loop():
            while self.is_running:
                try:
                    new_queues = self.check_for_new_videos(downloader, queue_manager, slack_notifier)
                    
                    for queue in new_queues:
                        downloader.download_queue(queue, queue_manager)
                    
                    if self.playlists:
                        min_interval = min(p.check_interval_minutes for p in self.playlists.values() if p.enabled)
                        time.sleep(min_interval * 60)
                    else:
                        time.sleep(300)
                
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


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "downloader_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.auto_detect_proxies()
        self.oauth_handler = OAuthHandler(self.config)
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AppConfig.from_dict(data)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
        
        return AppConfig()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
    
    def auto_detect_proxies(self):
        """Auto-detect proxies from proxies.txt or proxies.csv"""
        proxies = []
        
        if Path("proxies.txt").exists():
            try:
                with open("proxies.txt", 'r', encoding='utf-8') as f:
                    proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                console.print(f"[green]✓ Loaded {len(proxies)} proxies from proxies.txt[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read proxies.txt: {e}[/yellow]")
        
        elif Path("proxies.csv").exists():
            try:
                with open("proxies.csv", 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].strip() and not row[0].startswith('#'):
                            proxies.append(row[0].strip())
                console.print(f"[green]✓ Loaded {len(proxies)} proxies from proxies.csv[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read proxies.csv: {e}[/yellow]")
        
        if proxies:
            self.config.proxies = proxies
            self.save_config()
    
    def configure_authentication(self):
        """Configure authentication settings"""
        console.print("\n[cyan]Authentication Configuration[/cyan]")
        console.print("\nAuthentication methods:")
        console.print("  1. Browser cookies (cookies.txt) - Recommended")
        console.print("  2. OAuth2 (Complex setup required)\n")
        
        method = Prompt.ask("Select method", choices=["1", "2"], default="1")
        
        if method == "1":
            self._configure_cookies()
        else:
            self._configure_oauth()
    
    def _configure_cookies(self):
        """Configure cookie-based authentication"""
        console.print("\n[yellow]To export cookies:[/yellow]")
        console.print("1. Install browser extension:")
        console.print("   Chrome: 'Get cookies.txt LOCALLY'")
        console.print("   Firefox: 'cookies.txt'")
        console.print("2. Navigate to YouTube whilst logged in")
        console.print("3. Export cookies to a file")
        console.print("4. Enter the file path below\n")
        
        cookies_file = Prompt.ask("Cookies file path (or leave blank to skip)", default="")
        
        if cookies_file and Path(cookies_file).exists():
            self.config.cookies_file = cookies_file
            self.config.oauth_token = None
            console.print("[green]✓ Cookie authentication configured[/green]")
        elif cookies_file:
            console.print("[yellow]Warning: File not found, skipping[/yellow]")
        else:
            self.config.cookies_file = None
        
        self.save_config()
    
    def _configure_oauth(self):
        """Configure OAuth authentication"""
        if self.oauth_handler.authenticate():
            console.print("[green]✓ OAuth authenticated[/green]")
            self.save_config()
        else:
            console.print("[yellow]OAuth setup incomplete, falling back to cookies.txt[/yellow]")
    
    def configure_filename_template(self):
        """Configure default filename template"""
        console.print("\n[cyan]Filename Template Configuration[/cyan]")
        console.print(f"\nCurrent template: {self.config.default_filename_template}")
        console.print("\nAvailable placeholders:")
        console.print("  {title} - Video title")
        console.print("  {uploader} - Channel/uploader name")
        console.print("  {date} - Upload date")
        console.print("  {index} - Position in playlist")
        console.print("  {index:03d} - Zero-padded index (001, 002, etc.)")
        console.print("  {playlist} - Playlist name")
        console.print("  {video_id} - YouTube video ID\n")
        
        console.print("Example templates:")
        console.print("  {index:03d} - {title}")
        console.print("  {playlist} - {index:02d} - {title}")
        console.print("  {date} - {uploader} - {title}")
        console.print("  {title} [{video_id}]\n")
        
        template = Prompt.ask(
            "Enter template",
            default=self.config.default_filename_template
        )
        
        self.config.default_filename_template = template
        self.save_config()
        console.print("[green]✓ Template configured[/green]")
    
    def configure_slack(self):
        """Configure Slack webhook"""
        console.print("\n[cyan]Slack Notifications Configuration[/cyan]")
        console.print("\nTo get a Slack webhook URL:")
        console.print("  1. Go to https://api.slack.com/apps")
        console.print("  2. Create a new app or select existing")
        console.print("  3. Enable 'Incoming Webhooks'")
        console.print("  4. Add webhook to workspace")
        console.print("  5. Copy the webhook URL\n")
        
        if self.config.slack_webhook_url:
            console.print(f"[green]Current webhook:[/green] {self.config.slack_webhook_url[:50]}...")
            if Confirm.ask("Update webhook URL?", default=False):
                webhook = Prompt.ask("Slack webhook URL (or leave blank to disable)", default="")
                self.config.slack_webhook_url = webhook if webhook else None
        else:
            webhook = Prompt.ask("Slack webhook URL (or leave blank to skip)", default="")
            self.config.slack_webhook_url = webhook if webhook else None
        
        self.save_config()
        
        if self.config.slack_webhook_url:
            console.print("[green]✓ Slack notifications configured[/green]")
            
            # Test notification
            if Confirm.ask("Send test notification?", default=False):
                notifier = SlackNotifier(self.config.slack_webhook_url)
                if notifier.send_notification("Test", "Slack integration is working!", "good"):
                    console.print("[green]✓ Test notification sent successfully[/green]")
                else:
                    console.print("[red]✗ Failed to send test notification[/red]")
        else:
            console.print("[yellow]Slack notifications disabled[/yellow]")
    
    def manage_proxies(self):
        """Manage proxy list"""
        console.print("\n[cyan]Proxy Management[/cyan]")
        
        if self.config.proxies:
            console.print(f"\n[green]Current proxies: {len(self.config.proxies)}[/green]")
            for idx, proxy in enumerate(self.config.proxies[:10], 1):
                console.print(f"  {idx}. {proxy}")
            if len(self.config.proxies) > 10:
                console.print(f"  ... and {len(self.config.proxies) - 10} more")
        else:
            console.print("\n[yellow]No proxies configured[/yellow]")
            console.print("\nTo use proxies, create one of these files:")
            console.print("  • proxies.txt (one proxy per line)")
            console.print("  • proxies.csv (proxy,description format)\n")
        
        console.print("\nOptions:")
        console.print("  1. Reload proxies from file")
        console.print("  2. Remove a specific proxy")
        console.print("  3. Clear all proxies")
        console.print("  4. Back\n")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            self.auto_detect_proxies()
        elif choice == "2":
            self._remove_proxy()
        elif choice == "3":
            if Confirm.ask("Clear all proxies?", default=False):
                self.config.proxies = []
                console.print("[yellow]Proxies cleared[/yellow]")
                self.save_config()
    
    def _remove_proxy(self):
        """Remove a specific proxy"""
        if not self.config.proxies:
            console.print("[yellow]No proxies to remove[/yellow]")
            return
        
        console.print("\n[cyan]Select proxy to remove:[/cyan]")
        for idx, proxy in enumerate(self.config.proxies, 1):
            console.print(f"  {idx}. {proxy}")
        
        try:
            selection = IntPrompt.ask(
                "Proxy number (0 to cancel)",
                default=0
            )
            
            if selection > 0 and selection <= len(self.config.proxies):
                removed = self.config.proxies.pop(selection - 1)
                self.save_config()
                console.print(f"[green]✓ Removed proxy: {removed}[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def configure_workers(self):
        """Configure parallel download workers"""
        console.print("\n[cyan]Parallel Downloads Configuration[/cyan]")
        console.print(f"\nCurrent: {self.config.max_workers} parallel downloads")
        console.print("\nRecommendations:")
        console.print("  • 1-2 workers: Slow connection or rate limit concerns")
        console.print("  • 3-4 workers: Balanced (recommended)")
        console.print("  • 5+ workers: Fast connection, may trigger rate limits\n")
        
        workers = IntPrompt.ask(
            "Number of parallel downloads",
            default=self.config.max_workers
        )
        
        self.config.max_workers = max(1, min(10, workers))
        console.print(f"[green]✓ Set to {self.config.max_workers} workers[/green]")
        self.save_config()
    
    def configure_timeout(self):
        """Configure download timeout for long videos"""
        console.print("\n[cyan]Download Timeout Configuration[/cyan]")
        console.print(f"\nCurrent timeout: {self.config.download_timeout_minutes} minutes")
        console.print("\nRecommendations:")
        console.print("  • 60 minutes: Short videos only")
        console.print("  • 120 minutes: Standard (1-2 hour videos)")
        console.print("  • 240+ minutes: Long videos (4+ hours)\n")
        
        timeout = IntPrompt.ask(
            "Timeout in minutes",
            default=self.config.download_timeout_minutes
        )
        
        self.config.download_timeout_minutes = max(30, min(480, timeout))
        console.print(f"[green]✓ Set timeout to {self.config.download_timeout_minutes} minutes[/green]")
        self.save_config()


class QueueManager:
    """Manages download queues and persistence"""

    def __init__(self, queue_file: str = "download_queues.json", stats_manager: Optional[StatsManager] = None):
        self.queue_file = Path(queue_file)
        self.queues: Dict[str, DownloadQueue] = {}
        self.stats_manager = stats_manager
        self.load_queues()

    def load_queues(self):
        """Load queues from JSON file"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queues = {
                        qid: DownloadQueue.from_dict(qdata)
                        for qid, qdata in data.items()
                    }
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load queues: {e}[/yellow]")

    def save_queues(self):
        """Save queues to JSON file"""
        try:
            data = {qid: queue.to_dict() for qid, queue in self.queues.items()}
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[red]Error saving queues: {e}[/red]")

    def create_queue(self, playlist_url: str, playlist_title: str,
                     format_type: DownloadFormat, quality: str,
                     output_dir: str, items: List[DownloadItem],
                     download_order: str = "original",
                     filename_template: Optional[str] = None) -> str:
        """Create a new download queue"""
        queue_id = hashlib.md5(
            f"{playlist_url}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        queue = DownloadQueue(
            queue_id=queue_id,
            playlist_url=playlist_url,
            playlist_title=playlist_title,
            format_type=format_type,
            quality=quality,
            output_dir=output_dir,
            items=items,
            created_at=datetime.now().isoformat(),
            download_order=download_order,
            filename_template=filename_template
        )

        self.queues[queue_id] = queue
        self.save_queues()
        
        # Record stats
        if self.stats_manager:
            self.stats_manager.record_queue_created(len(items))
        
        return queue_id

    def get_queue(self, queue_id: str) -> Optional[DownloadQueue]:
        """Get a queue by ID"""
        return self.queues.get(queue_id)

    def update_queue(self, queue_id: str, queue: DownloadQueue):
        """Update a queue"""
        self.queues[queue_id] = queue
        self.save_queues()

    def list_incomplete_queues(self) -> List[DownloadQueue]:
        """Get all incomplete queues"""
        incomplete = []
        for queue in self.queues.values():
            if queue and queue.items:
                if any(item.status != DownloadStatus.COMPLETED for item in queue.items):
                    incomplete.append(queue)
        return incomplete
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        total_queues = len(self.queues)
        total_items = sum(len(q.items) for q in self.queues.values())
        completed_items = sum(
            1 for q in self.queues.values() 
            for item in q.items 
            if item.status == DownloadStatus.COMPLETED
        )
        failed_items = sum(
            1 for q in self.queues.values() 
            for item in q.items 
            if item.status == DownloadStatus.FAILED
        )
        
        total_time = sum(
            item.download_duration_seconds or 0
            for q in self.queues.values()
            for item in q.items
        )
        
        return {
            'total_queues': total_queues,
            'total_items': total_items,
            'completed_items': completed_items,
            'failed_items': failed_items,
            'pending_items': total_items - completed_items - failed_items,
            'total_time': total_time
        }


class PlaylistDownloader:
    """Handles playlist downloading operations"""

    def __init__(self, config: AppConfig, stats_manager: Optional[StatsManager] = None, 
                 slack_notifier: Optional[SlackNotifier] = None):
        self.config = config
        self.console = console
        self.proxy_manager = ProxyManager(config.proxies)
        self.stats_manager = stats_manager
        self.slack_notifier = slack_notifier

    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            console.print("[red]FFmpeg not found![/red]")
            console.print("[yellow]Audio conversion requires FFmpeg to be installed.[/yellow]")
            console.print("\n[cyan]Install FFmpeg:[/cyan]")
            console.print("  Ubuntu/Debian: sudo apt install ffmpeg")
            console.print("  macOS: brew install ffmpeg")
            console.print("  Windows: choco install ffmpeg or download from ffmpeg.org\n")
            return False
        return True

    def _get_base_ydl_opts(self, use_proxy: bool = True) -> Dict:
        """Get base yt-dlp options with authentication and proxy"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': self.config.download_timeout_minutes * 60,
        }
        
        if self.config.cookies_file and Path(self.config.cookies_file).exists():
            opts['cookiefile'] = self.config.cookies_file
        
        if use_proxy and self.config.proxies:
            proxy = self.proxy_manager.get_random_proxy()
            if proxy:
                opts['proxy'] = proxy
        
        return opts

    def get_playlist_info(self, url: str) -> Optional[Dict]:
        """Extract playlist information"""
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts['extract_flat'] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            console.print(f"[red]Error extracting playlist info: {e}[/red]")
            return None

    def search_channel_playlists(self, channel_url: str) -> List[Dict]:
        """Search for playlists in a channel"""
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts['extract_flat'] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)

                if not info:
                    return []

                entries = info.get('entries', [])
                if entries is None:
                    entries = []

                if entries:
                    playlists = []
                    for entry in entries:
                        if entry and entry.get('_type') == 'playlist':
                            playlists.append({
                                'title': entry.get('title', 'Unknown'),
                                'url': entry.get('url', ''),
                                'playlist_count': entry.get('playlist_count', 0)
                            })
                    
                    if playlists:
                        return playlists

                channel_id = info.get('channel_id') or info.get('id')
                if channel_id:
                    playlists_url = f"https://www.youtube.com/channel/{channel_id}/playlists"
                    return self.search_channel_playlists(playlists_url)

        except Exception as e:
            console.print(f"[red]Error searching channel: {e}[/red]")

        return []

    def download_item(self, item: DownloadItem, format_type: DownloadFormat,
                      quality: str, output_dir: str, filename_template: Optional[str] = None,
                      index: int = 0, playlist_title: str = "") -> DownloadItem:
        """Download a single item"""
        item.status = DownloadStatus.DOWNLOADING
        item.download_started_at = datetime.now().isoformat()
        start_time = datetime.now()

        if filename_template:
            base_filename = FileRenamer.apply_template(
                filename_template, item, index, playlist_title
            )
        else:
            base_filename = FileRenamer.sanitize_filename(item.title)

        ydl_opts = self._get_base_ydl_opts()
        
        # Add progress hook for long videos
        def progress_hook(d):
            if d['status'] == 'downloading':
                # This helps track progress for very long downloads
                pass

        ydl_opts['progress_hooks'] = [progress_hook]

        if format_type == DownloadFormat.AUDIO:
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
            ydl_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegMetadata',
                }
            ]
            ydl_opts['outtmpl'] = f'{output_dir}/{base_filename}.%(ext)s'
            ydl_opts['writethumbnail'] = False
            ydl_opts['keepvideo'] = False
            ydl_opts['prefer_ffmpeg'] = True
        else:
            if quality == 'best':
                format_str = 'bestvideo+bestaudio/best'
            elif quality == 'worst':
                format_str = 'worstvideo+worstaudio/worst'
            else:
                format_str = f'bestvideo[height<={quality.replace("p", "")}]+bestaudio/best[height<={quality.replace("p", "")}]'

            ydl_opts['format'] = format_str
            ydl_opts['outtmpl'] = f'{output_dir}/{base_filename}.%(ext)s'
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=True)
                
                if not item.upload_date:
                    item.upload_date = info.get('upload_date')
                if not item.uploader:
                    item.uploader = info.get('uploader')
                if not item.video_id:
                    item.video_id = info.get('id')
                
                if format_type == DownloadFormat.AUDIO:
                    filename = f"{output_dir}/{base_filename}.mp3"
                    
                    if not Path(filename).exists():
                        possible_files = list(Path(output_dir).glob(f"{base_filename}.*"))
                        if possible_files:
                            filename = str(possible_files[0])
                else:
                    filename = ydl.prepare_filename(info)

                item.file_path = str(filename)
                
                # Get file size
                if Path(filename).exists():
                    item.file_size_bytes = Path(filename).stat().st_size
                
                item.file_hash = self._calculate_file_hash(filename)
                item.status = DownloadStatus.COMPLETED
                
                end_time = datetime.now()
                item.download_completed_at = end_time.isoformat()
                item.download_duration_seconds = (end_time - start_time).total_seconds()
                
                # Record stats
                if self.stats_manager:
                    self.stats_manager.record_download(True, item.download_duration_seconds, item.file_size_bytes or 0)

        except Exception as e:
            item.status = DownloadStatus.FAILED
            item.error = str(e)
            
            end_time = datetime.now()
            item.download_completed_at = end_time.isoformat()
            item.download_duration_seconds = (end_time - start_time).total_seconds()
            
            # Record failed stats
            if self.stats_manager:
                self.stats_manager.record_download(False, item.download_duration_seconds, 0)

        return item

    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    def _format_duration(self, seconds: Optional[float]) -> str:
        """Format duration in human-readable format"""
        if seconds is None:
            return "N/A"
        
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _format_size(self, bytes_size: Optional[int]) -> str:
        """Format file size in human-readable format"""
        if bytes_size is None or bytes_size == 0:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def _sort_items(self, items: List[DownloadItem], order: str) -> List[DownloadItem]:
        """Sort items based on download order"""
        if order == "newest_first":
            return list(reversed(items))
        elif order == "oldest_first":
            return items
        else:
            return items

    def download_queue(self, queue: DownloadQueue, queue_manager: QueueManager):
        """Download all items in a queue with parallel processing"""
        
        stuck_items = [item for item in queue.items if item.status == DownloadStatus.DOWNLOADING]
        if stuck_items:
            console.print(f"\n[yellow]Found {len(stuck_items)} items stuck in 'downloading' state[/yellow]")
            console.print("[yellow]Resetting them to 'pending' for retry...[/yellow]\n")
            for item in stuck_items:
                item.status = DownloadStatus.PENDING
            queue_manager.update_queue(queue.queue_id, queue)
        
        pending_items = [
            item for item in queue.items
            if item.status in (DownloadStatus.PENDING, DownloadStatus.FAILED)
        ]

        if not pending_items:
            console.print("[green]All items already downloaded![/green]")
            return

        pending_items = self._sort_items(pending_items, queue.download_order)

        info_panel = Panel(
            f"[cyan]Playlist:[/cyan] {queue.playlist_title}\n"
            f"[cyan]Items:[/cyan] {len(pending_items)}\n"
            f"[cyan]Workers:[/cyan] {self.config.max_workers}\n"
            f"[cyan]Order:[/cyan] {queue.download_order}\n"
            f"[cyan]Format:[/cyan] {queue.format_type.value}\n"
            f"[cyan]Timeout:[/cyan] {self.config.download_timeout_minutes} minutes",
            title="[bold]Download Queue[/bold]",
            border_style="cyan"
        )
        console.print(info_panel)

        queue_start_time = datetime.now()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            task = progress.add_task(
                f"Downloading {queue.playlist_title}",
                total=len(pending_items)
            )

            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_item = {}
                for idx, item in enumerate(pending_items, 1):
                    future = executor.submit(
                        self.download_item,
                        item,
                        queue.format_type,
                        queue.quality,
                        queue.output_dir,
                        queue.filename_template,
                        idx,
                        queue.playlist_title
                    )
                    future_to_item[future] = item

                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        updated_item = future.result()
                        idx = queue.items.index(item)
                        queue.items[idx] = updated_item

                        duration_str = self._format_duration(updated_item.download_duration_seconds)
                        size_str = self._format_size(updated_item.file_size_bytes)

                        if updated_item.status == DownloadStatus.COMPLETED:
                            progress.console.print(
                                f"[green]✓[/green] {updated_item.title} [dim]({duration_str}, {size_str})[/dim]"
                            )
                        else:
                            progress.console.print(
                                f"[red]✗[/red] {updated_item.title} [dim]({duration_str})[/dim]: {updated_item.error}"
                            )

                    except Exception as e:
                        progress.console.print(f"[red]Error: {e}[/red]")

                    progress.update(task, advance=1)
                    queue_manager.update_queue(queue.queue_id, queue)

        queue.completed_at = datetime.now().isoformat()
        queue_manager.update_queue(queue.queue_id, queue)
        
        # Record queue completion
        if self.stats_manager:
            self.stats_manager.record_queue_completed()

        self._print_summary(queue, queue_start_time)
        self._check_duplicates(queue)
        
        # Send Slack notification
        if self.slack_notifier and self.slack_notifier.is_configured():
            completed = sum(1 for item in queue.items if item.status == DownloadStatus.COMPLETED)
            failed = sum(1 for item in queue.items if item.status == DownloadStatus.FAILED)
            total_duration = (datetime.now() - queue_start_time).total_seconds()
            
            self.slack_notifier.notify_queue_completed(
                queue.playlist_title,
                completed,
                failed,
                len(queue.items),
                self._format_duration(total_duration)
            )

    def _print_summary(self, queue: DownloadQueue, queue_start_time: datetime):
        """Print download summary with timing information"""
        completed = [item for item in queue.items if item.status == DownloadStatus.COMPLETED]
        failed = [item for item in queue.items if item.status == DownloadStatus.FAILED]

        total_time = sum(
            item.download_duration_seconds 
            for item in queue.items 
            if item.download_duration_seconds is not None
        )
        
        total_size = sum(
            item.file_size_bytes or 0
            for item in completed
        )

        completed_times = [
            item.download_duration_seconds 
            for item in completed 
            if item.download_duration_seconds is not None
        ]
        avg_time = sum(completed_times) / len(completed_times) if completed_times else 0
        
        queue_duration = (datetime.now() - queue_start_time).total_seconds()

        table = Table(title="Download Summary", show_header=True, header_style="bold cyan")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Details", style="yellow")

        table.add_row("✓ Completed", f"[green]{len(completed)}[/green]", 
                     f"Avg: {self._format_duration(avg_time)}")
        table.add_row("✗ Failed", f"[red]{len(failed)}[/red]", "")
        table.add_row("Total", str(len(queue.items)), 
                     f"Time: {self._format_duration(total_time)}")
        table.add_row("Size", "", f"{self._format_size(total_size)}")
        table.add_row("Queue Duration", "", f"{self._format_duration(queue_duration)}")

        console.print("\n")
        console.print(table)

        if len(completed) > 3:
            sorted_completed = sorted(
                completed, 
                key=lambda x: x.download_duration_seconds or 0, 
                reverse=True
            )
            
            slowest_panel = Panel(
                "\n".join([
                    f"• {item.title}: {self._format_duration(item.download_duration_seconds)} ({self._format_size(item.file_size_bytes)})"
                    for item in sorted_completed[:3]
                ]),
                title="[bold yellow]Slowest Downloads[/bold yellow]",
                border_style="yellow"
            )
            console.print("\n")
            console.print(slowest_panel)

    def _check_duplicates(self, queue: DownloadQueue):
        """Check for duplicate files by hash"""
        hash_to_items = {}

        for item in queue.items:
            if item.status == DownloadStatus.COMPLETED and item.file_hash:
                if item.file_hash not in hash_to_items:
                    hash_to_items[item.file_hash] = []
                hash_to_items[item.file_hash].append(item)

        duplicates = {h: items for h, items in hash_to_items.items() if len(items) > 1}

        if duplicates:
            console.print("\n")
            dup_panel = Panel(
                "\n\n".join([
                    f"[yellow]Hash: {hash_val[:12]}...[/yellow]\n" + 
                    "\n".join([f"  • {item.title}" for item in items])
                    for hash_val, items in duplicates.items()
                ]),
                title="[bold yellow]Duplicate Files Detected[/bold yellow]",
                border_style="yellow"
            )
            console.print(dup_panel)

            if Confirm.ask("\nRemove duplicate files? (keep first occurrence)"):
                self._remove_duplicates(duplicates)

    def _remove_duplicates(self, duplicates: Dict[str, List[DownloadItem]]):
        """Remove duplicate files, keeping the first one"""
        for items in duplicates.values():
            for item in items[1:]:
                try:
                    if item.file_path and Path(item.file_path).exists():
                        Path(item.file_path).unlink()
                        console.print(f"[green]Removed:[/green] {item.file_path}")
                except Exception as e:
                    console.print(f"[red]Error removing {item.file_path}: {e}[/red]")


def create_dashboard_layout(queue_manager: QueueManager, 
                            monitor_manager: MonitorManager,
                            stats_manager: StatsManager) -> Layout:
    """Create dashboard layout with statistics"""
    layout = Layout()
    
    stats = queue_manager.get_statistics()
    daily_summary = stats_manager.get_summary(7)  # Last 7 days
    
    # Queue statistics panel
    stats_content = (
        f"[cyan]Total Queues:[/cyan] {stats['total_queues']}\n"
        f"[green]Completed:[/green] {stats['completed_items']}\n"
        f"[yellow]Pending:[/yellow] {stats['pending_items']}\n"
        f"[red]Failed:[/red] {stats['failed_items']}\n"
        f"[blue]Total Time:[/blue] {PlaylistDownloader(AppConfig())._format_duration(stats['total_time'])}"
    )
    
    stats_panel = Panel(
        stats_content,
        title="[bold]Queue Statistics[/bold]",
        border_style="cyan"
    )
    
    # Daily statistics panel
    daily_content = (
        f"[cyan]Last 7 Days:[/cyan]\n"
        f"[green]Downloaded:[/green] {daily_summary['total_downloaded']}\n"
        f"[yellow]Queued:[/yellow] {daily_summary['total_queued']}\n"
        f"[red]Failed:[/red] {daily_summary['total_failed']}\n"
        f"[blue]Avg/Day:[/blue] {daily_summary['avg_downloads_per_day']:.1f}\n"
        f"[magenta]Size:[/magenta] {PlaylistDownloader(AppConfig())._format_size(daily_summary['total_size_bytes'])}"
    )
    
    daily_panel = Panel(
        daily_content,
        title="[bold]Daily Statistics[/bold]",
        border_style="green"
    )
    
    # Monitoring status panel
    monitor_status = "Running" if monitor_manager.is_running else "Stopped"
    monitor_color = "green" if monitor_manager.is_running else "red"
    monitored_count = len(monitor_manager.playlists)
    
    monitor_content = (
        f"[{monitor_color}]Status:[/{monitor_color}] {monitor_status}\n"
        f"[cyan]Monitored Playlists:[/cyan] {monitored_count}"
    )
    
    monitor_panel = Panel(
        monitor_content,
        title="[bold]Monitoring[/bold]",
        border_style=monitor_color
    )
    
    layout.split_row(
        Layout(stats_panel),
        Layout(daily_panel),
        Layout(monitor_panel)
    )
    
    return layout


def display_statistics(stats_manager: StatsManager):
    """Display detailed statistics"""
    console.print("\n")
    
    summary_7 = stats_manager.get_summary(7)
    summary_30 = stats_manager.get_summary(30)
    
    # Summary table
    table = Table(title="Statistics Summary", show_header=True, header_style="bold cyan")
    table.add_column("Period", style="cyan")
    table.add_column("Downloaded", style="green", justify="right")
    table.add_column("Queued", style="yellow", justify="right")
    table.add_column("Failed", style="red", justify="right")
    table.add_column("Avg/Day", style="blue", justify="right")
    table.add_column("Total Size", style="magenta")
    
    downloader = PlaylistDownloader(AppConfig())
    
    table.add_row(
        "Last 7 Days",
        str(summary_7['total_downloaded']),
        str(summary_7['total_queued']),
        str(summary_7['total_failed']),
        f"{summary_7['avg_downloads_per_day']:.1f}",
        downloader._format_size(summary_7['total_size_bytes'])
    )
    
    table.add_row(
        "Last 30 Days",
        str(summary_30['total_downloaded']),
        str(summary_30['total_queued']),
        str(summary_30['total_failed']),
        f"{summary_30['avg_downloads_per_day']:.1f}",
        downloader._format_size(summary_30['total_size_bytes'])
    )
    
    console.print(table)
    
    # Daily breakdown
    console.print("\n")
    daily_stats = stats_manager.get_date_range_stats(14)
    
    daily_table = Table(title="Last 14 Days", show_header=True, header_style="bold cyan")
    daily_table.add_column("Date", style="cyan")
    daily_table.add_column("Downloaded", style="green", justify="right")
    daily_table.add_column("Failed", style="red", justify="right")
    daily_table.add_column("Time", style="blue")
    daily_table.add_column("Size", style="magenta")
    
    for stat in reversed(daily_stats):
        if stat.videos_downloaded > 0 or stat.videos_failed > 0:
            daily_table.add_row(
                stat.date,
                str(stat.videos_downloaded),
                str(stat.videos_failed),
                downloader._format_duration(stat.total_download_time_seconds),
                downloader._format_size(stat.total_file_size_bytes)
            )
    
    console.print(daily_table)


def display_menu() -> str:
    """Display main menu with enhanced UI"""
    console.print("\n")
    
    title = Panel.fit(
        "[bold cyan]Playlist Downloader Pro[/bold cyan]\n"
        "Advanced video/audio playlist management",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(title)

    options = [
        ("1", "📥 Download new playlist"),
        ("2", "▶️  Resume incomplete download"),
        ("3", "🔍 Search channel for playlists"),
        ("4", "📊 View queue status"),
        ("5", "📈 View statistics"),
        ("6", "👁️  Monitoring"),
        ("7", "⚙️  Settings"),
        ("8", "🚪 Exit")
    ]

    option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
    
    menu_panel = Panel(
        option_text,
        title="[bold]Main Menu[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(menu_panel)

    choice = Prompt.ask(
        "\n[bold cyan]Select an option[/bold cyan]",
        choices=[num for num, _ in options],
        default="1"
    )

    return choice


def display_settings_menu(config_manager: ConfigManager):
    """Display settings menu with enhanced UI"""
    while True:
        console.print("\n")
        
        auth_status = "✓ Enabled" if config_manager.config.cookies_file else "✗ Disabled"
        proxy_status = f"✓ {len(config_manager.config.proxies)} proxies" if config_manager.config.proxies else "✗ Disabled"
        slack_status = "✓ Enabled" if config_manager.config.slack_webhook_url else "✗ Disabled"
        
        settings_table = Table(show_header=False, box=None, padding=(0, 2))
        settings_table.add_column("Setting", style="yellow", no_wrap=True)
        settings_table.add_column("Value", style="white")
        
        settings_table.add_row("Authentication", auth_status)
        settings_table.add_row("Proxies", proxy_status)
        settings_table.add_row("Parallel Downloads", str(config_manager.config.max_workers))
        settings_table.add_row("Filename Template", config_manager.config.default_filename_template)
        settings_table.add_row("Slack Notifications", slack_status)
        settings_table.add_row("Download Timeout", f"{config_manager.config.download_timeout_minutes} minutes")
        
        settings_panel = Panel(
            settings_table,
            title="[bold]Current Settings[/bold]",
            border_style="cyan"
        )
        console.print(settings_panel)
        
        options = [
            ("1", "🔐 Configure authentication"),
            ("2", "🌐 Manage proxies"),
            ("3", "⚡ Configure parallel downloads"),
            ("4", "📝 Configure filename template"),
            ("5", "💬 Configure Slack notifications"),
            ("6", "⏱️  Configure download timeout"),
            ("7", "🔙 Back to main menu")
        ]
        
        option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
        console.print(f"\n{option_text}\n")
        
        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=[num for num, _ in options],
            default="7"
        )
        
        if choice == "1":
            config_manager.configure_authentication()
        elif choice == "2":
            config_manager.manage_proxies()
        elif choice == "3":
            config_manager.configure_workers()
        elif choice == "4":
            config_manager.configure_filename_template()
        elif choice == "5":
            config_manager.configure_slack()
        elif choice == "6":
            config_manager.configure_timeout()
        elif choice == "7":
            break


def display_monitoring_menu(monitor_manager: MonitorManager, 
                           downloader: PlaylistDownloader,
                           queue_manager: QueueManager,
                           config_manager: ConfigManager,
                           slack_notifier: SlackNotifier):
    """Display monitoring menu"""
    while True:
        console.print("\n")
        
        status = "🟢 Running" if monitor_manager.is_running else "🔴 Stopped"
        
        status_panel = Panel(
            f"[bold]Status:[/bold] {status}\n"
            f"[cyan]Monitored Playlists:[/cyan] {len(monitor_manager.playlists)}",
            title="[bold]Monitoring Status[/bold]",
            border_style="cyan"
        )
        console.print(status_panel)
        
        if monitor_manager.playlists:
            playlist_table = Table(title="Monitored Playlists", show_header=True)
            playlist_table.add_column("Title", style="cyan")
            playlist_table.add_column("Format", style="yellow")
            playlist_table.add_column("Interval", style="green")
            playlist_table.add_column("Last Checked", style="white")
            playlist_table.add_column("Status", style="magenta")
            
            for playlist in monitor_manager.playlists.values():
                last_checked = playlist.last_checked or "Never"
                if playlist.last_checked:
                    dt = datetime.fromisoformat(playlist.last_checked)
                    last_checked = dt.strftime("%Y-%m-%d %H:%M")
                
                status_emoji = "✓" if playlist.enabled else "✗"
                
                playlist_table.add_row(
                    playlist.playlist_title[:40],
                    playlist.format_type.value,
                    f"{playlist.check_interval_minutes}m",
                    last_checked,
                    status_emoji
                )
            
            console.print("\n")
            console.print(playlist_table)
        
        options = [
            ("1", "➕ Add playlist to monitoring"),
            ("2", "➖ Remove playlist from monitoring"),
            ("3", "▶️  Start monitoring"),
            ("4", "⏸️  Stop monitoring"),
            ("5", "🔄 Check now"),
            ("6", "🔙 Back to main menu")
        ]
        
        option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
        console.print(f"\n{option_text}\n")
        
        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=[num for num, _ in options],
            default="6"
        )
        
        if choice == "1":
            add_playlist_to_monitoring(monitor_manager, downloader, config_manager)
        elif choice == "2":
            remove_playlist_from_monitoring(monitor_manager)
        elif choice == "3":
            monitor_manager.start_monitoring(downloader, queue_manager, slack_notifier)
        elif choice == "4":
            monitor_manager.stop_monitoring()
        elif choice == "5":
            console.print("\n[yellow]Checking for new videos...[/yellow]")
            new_queues = monitor_manager.check_for_new_videos(downloader, queue_manager, slack_notifier)
            if new_queues:
                console.print(f"[green]Found {len(new_queues)} new video(s)[/green]")
                if Confirm.ask("Download now?", default=True):
                    for queue in new_queues:
                        downloader.download_queue(queue, queue_manager)
            else:
                console.print("[yellow]No new videos found[/yellow]")
        elif choice == "6":
            break


def add_playlist_to_monitoring(monitor_manager: MonitorManager, 
                               downloader: PlaylistDownloader,
                               config_manager: ConfigManager):
    """Add a playlist to monitoring"""
    playlist_url = Prompt.ask("\n[cyan]Enter playlist URL[/cyan]")
    
    console.print("\n[yellow]Fetching playlist information...[/yellow]")
    playlist_info = downloader.get_playlist_info(playlist_url)
    
    if not playlist_info:
        console.print("[red]Failed to fetch playlist information[/red]")
        return
    
    playlist_title = playlist_info.get('title', 'Unknown Playlist')
    console.print(f"\n[green]Found playlist:[/green] {playlist_title}")
    
    format_choice = Prompt.ask(
        "Download format",
        choices=["video", "audio"],
        default="video"
    )
    format_type = DownloadFormat.VIDEO if format_choice == "video" else DownloadFormat.AUDIO
    
    quality = get_quality_choice(format_type)
    
    default_dir = f"downloads/{playlist_title}"
    output_dir = Prompt.ask("Output directory", default=default_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    interval = IntPrompt.ask("Check interval (minutes)", default=60)
    
    use_template = Confirm.ask(
        f"Use filename template? (default: {config_manager.config.default_filename_template})",
        default=True
    )
    filename_template = config_manager.config.default_filename_template if use_template else None
    
    download_order = get_download_order()
    
    monitored_playlist = MonitoredPlaylist(
        playlist_url=playlist_url,
        playlist_title=playlist_title,
        format_type=format_type,
        quality=quality,
        output_dir=output_dir,
        check_interval_minutes=interval,
        filename_template=filename_template,
        download_order=download_order
    )
    
    monitor_manager.add_playlist(monitored_playlist)
    console.print(f"\n[green]✓ Added {playlist_title} to monitoring[/green]")


def remove_playlist_from_monitoring(monitor_manager: MonitorManager):
    """Remove a playlist from monitoring"""
    if not monitor_manager.playlists:
        console.print("\n[yellow]No monitored playlists[/yellow]")
        return
    
    console.print("\n[cyan]Monitored Playlists:[/cyan]")
    playlists_list = list(monitor_manager.playlists.items())
    
    for idx, (url, playlist) in enumerate(playlists_list, 1):
        console.print(f"  {idx}. {playlist.playlist_title}")
    
    selection = IntPrompt.ask(
        "Select playlist to remove (0 to cancel)",
        default=0
    )
    
    if selection > 0 and selection <= len(playlists_list):
        url, playlist = playlists_list[selection - 1]
        monitor_manager.remove_playlist(url)
        console.print(f"[green]✓ Removed {playlist.playlist_title} from monitoring[/green]")


def get_quality_choice(format_type: DownloadFormat) -> str:
    """Get quality selection from user"""
    if format_type == DownloadFormat.AUDIO:
        return "192"

    console.print("\n[cyan]Video Quality Options:[/cyan]")
    qualities = ["best", "1080p", "720p", "480p", "360p", "worst"]

    for idx, quality in enumerate(qualities, 1):
        console.print(f"  {idx}. {quality}")

    choice = Prompt.ask(
        "Select quality",
        choices=[str(i) for i in range(1, len(qualities) + 1)],
        default="1"
    )

    return qualities[int(choice) - 1]


def get_download_order() -> str:
    """Get download order preference from user"""
    console.print("\n[cyan]Download Order:[/cyan]")
    orders = [
        ("original", "Original playlist order"),
        ("oldest_first", "Oldest to newest"),
        ("newest_first", "Newest to oldest")
    ]

    for idx, (value, description) in enumerate(orders, 1):
        console.print(f"  {idx}. {description}")

    choice = Prompt.ask(
        "Select order",
        choices=[str(i) for i in range(1, len(orders) + 1)],
        default="1"
    )

    return orders[int(choice) - 1][0]


def main():
    """Main application entry point"""
    stats_manager = StatsManager()
    config_manager = ConfigManager()
    slack_notifier = SlackNotifier(config_manager.config.slack_webhook_url)
    queue_manager = QueueManager(stats_manager=stats_manager)
    monitor_manager = MonitorManager()
    downloader = PlaylistDownloader(config_manager.config, stats_manager, slack_notifier)
    
    if config_manager.config.monitoring_enabled and monitor_manager.playlists:
        monitor_manager.start_monitoring(downloader, queue_manager, slack_notifier)

    while True:
        choice = display_menu()

        if choice == "1":
            playlist_url = Prompt.ask("\n[cyan]Enter playlist URL[/cyan]")

            console.print("\n[yellow]Fetching playlist information...[/yellow]")
            playlist_info = downloader.get_playlist_info(playlist_url)

            if not playlist_info:
                console.print("[red]Failed to fetch playlist information[/red]")
                console.print("[yellow]Tip: Configure authentication in Settings if needed[/yellow]")
                continue

            playlist_title = playlist_info.get('title', 'Unknown Playlist')
            
            entries = playlist_info.get('entries')
            if entries is None:
                entries = []
            
            entries = [e for e in entries if e is not None]

            if not entries:
                console.print("[red]No entries found in playlist[/red]")
                continue

            info_panel = Panel(
                f"[green]Playlist:[/green] {playlist_title}\n"
                f"[green]Total items:[/green] {len(entries)}",
                title="[bold]Playlist Info[/bold]",
                border_style="green"
            )
            console.print("\n")
            console.print(info_panel)

            if len(entries) > 50:
                if Confirm.ask(f"\nLimit downloads from {len(entries)} items?"):
                    limit = IntPrompt.ask("How many items to download?", default=50)
                    entries = entries[:limit]

            format_choice = Prompt.ask(
                "\nDownload format",
                choices=["video", "audio"],
                default="video"
            )
            format_type = DownloadFormat.VIDEO if format_choice == "video" else DownloadFormat.AUDIO

            if format_type == DownloadFormat.AUDIO:
                if not downloader.check_ffmpeg():
                    console.print("[red]Cannot proceed without FFmpeg[/red]")
                    continue

            quality = get_quality_choice(format_type)
            download_order = get_download_order()

            use_template = Confirm.ask(
                f"\nUse filename template? (default: {config_manager.config.default_filename_template})",
                default=True
            )
            filename_template = config_manager.config.default_filename_template if use_template else None

            default_dir = f"downloads/{playlist_title}"
            output_dir = Prompt.ask("\nOutput directory", default=default_dir)
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            items = []
            for entry in entries:
                if not entry:
                    continue
                
                url = entry.get('url', '')
                title = entry.get('title', 'Unknown')
                
                if not url:
                    continue
                
                items.append(DownloadItem(
                    url=url,
                    title=title,
                    status=DownloadStatus.PENDING,
                    upload_date=entry.get('upload_date'),
                    uploader=entry.get('uploader'),
                    video_id=entry.get('id')
                ))

            if not items:
                console.print("[red]No valid items found[/red]")
                continue

            queue_id = queue_manager.create_queue(
                playlist_url=playlist_url,
                playlist_title=playlist_title,
                format_type=format_type,
                quality=quality,
                output_dir=output_dir,
                items=items,
                download_order=download_order,
                filename_template=filename_template
            )

            console.print(f"\n[green]✓ Queue created:[/green] {queue_id}")

            if Confirm.ask("\nStart download now?", default=True):
                queue = queue_manager.get_queue(queue_id)
                downloader.download_queue(queue, queue_manager)

        elif choice == "2":
            incomplete = queue_manager.list_incomplete_queues()

            if not incomplete:
                console.print("\n[yellow]No incomplete queues found[/yellow]")
                continue

            console.print("\n")
            queue_table = Table(title="Incomplete Queues")
            queue_table.add_column("#", style="cyan")
            queue_table.add_column("Playlist", style="magenta")
            queue_table.add_column("Pending", style="yellow", justify="right")
            queue_table.add_column("Failed", style="red", justify="right")
            
            for idx, queue in enumerate(incomplete, 1):
                pending = sum(1 for item in queue.items if item.status == DownloadStatus.PENDING)
                failed = sum(1 for item in queue.items if item.status == DownloadStatus.FAILED)
                queue_table.add_row(str(idx), queue.playlist_title[:40], str(pending), str(failed))
            
            console.print(queue_table)

            selection = IntPrompt.ask(
                "\nSelect queue",
                default=1,
                choices=[str(i) for i in range(1, len(incomplete) + 1)]
            )

            queue = incomplete[selection - 1]

            if Confirm.ask("\nRestart downloads?", default=True):
                downloader = PlaylistDownloader(config_manager.config, stats_manager, slack_notifier)
                downloader.download_queue(queue, queue_manager)

        elif choice == "3":
            channel_url = Prompt.ask("\n[cyan]Enter channel URL[/cyan]")

            console.print("\n[yellow]Searching for playlists...[/yellow]")
            playlists = downloader.search_channel_playlists(channel_url)

            if not playlists:
                console.print("[red]No playlists found[/red]")
                continue

            console.print(f"\n[green]Found {len(playlists)} playlists:[/green]\n")
            for idx, playlist in enumerate(playlists, 1):
                count = playlist.get('playlist_count', 'Unknown')
                console.print(f"  {idx}. {playlist['title']} ({count} items)")

            if playlists:
                selection = IntPrompt.ask(
                    "\nSelect playlist (0 to cancel)",
                    default=0
                )

                if selection > 0 and selection <= len(playlists):
                    selected = playlists[selection - 1]
                    info_panel = Panel(
                        f"[cyan]Title:[/cyan] {selected['title']}\n"
                        f"[cyan]URL:[/cyan] {selected['url']}",
                        title="[bold]Selected Playlist[/bold]",
                        border_style="green"
                    )
                    console.print("\n")
                    console.print(info_panel)

        elif choice == "4":
            if not queue_manager.queues:
                console.print("\n[yellow]No queues found[/yellow]")
                continue

            dashboard = create_dashboard_layout(queue_manager, monitor_manager, stats_manager)
            console.print("\n")
            console.print(dashboard)

            table = Table(title="\nDownload Queues", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="cyan")
            table.add_column("Playlist", style="magenta")
            table.add_column("Format", style="yellow")
            table.add_column("✓", style="green", justify="right")
            table.add_column("✗", style="red", justify="right")
            table.add_column("Total", style="blue", justify="right")
            table.add_column("Time", style="white")

            for queue_id, queue in queue_manager.queues.items():
                completed = sum(1 for item in queue.items if item.status == DownloadStatus.COMPLETED)
                failed = sum(1 for item in queue.items if item.status == DownloadStatus.FAILED)
                
                total_time = sum(
                    item.download_duration_seconds or 0
                    for item in queue.items
                )
                time_str = downloader._format_duration(total_time) if total_time > 0 else "N/A"

                table.add_row(
                    queue_id[:8],
                    queue.playlist_title[:35],
                    queue.format_type.value,
                    str(completed),
                    str(failed),
                    str(len(queue.items)),
                    time_str
                )

            console.print("\n")
            console.print(table)

        elif choice == "5":
            display_statistics(stats_manager)

        elif choice == "6":
            display_monitoring_menu(monitor_manager, downloader, queue_manager, config_manager, slack_notifier)

        elif choice == "7":
            display_settings_menu(config_manager)
            downloader = PlaylistDownloader(config_manager.config, stats_manager, slack_notifier)
            slack_notifier = SlackNotifier(config_manager.config.slack_webhook_url)

        elif choice == "8":
            if monitor_manager.is_running:
                monitor_manager.stop_monitoring()
            console.print("\n[cyan]Goodbye![/cyan]\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
