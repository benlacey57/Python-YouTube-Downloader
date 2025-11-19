"""Base downloader with shared functionality"""
import yt_dlp
import hashlib
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from rich.console import Console

from managers.config_manager import AppConfig
from managers.stats_manager import StatsManager
from managers.notification_manager import NotificationManager
from models.download_item import DownloadItem
from models.queue import Queue
from enums import DownloadStatus
from utils.rate_limiter import RateLimiter
from utils.keyboard_handler import keyboard_handler

console = Console()


class BaseDownloader(ABC):
    """Base class for all downloaders"""
    
    def __init__(self, config: AppConfig, stats_manager: StatsManager = None,
                 notification_manager: NotificationManager = None):
        self.config = config
        self.stats_manager = stats_manager
        self.notification_manager = notification_manager
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_downloads_per_hour=config.max_downloads_per_hour,
            min_delay_seconds=config.min_delay_seconds,
            max_delay_seconds=config.max_delay_seconds
        )
    
    def get_base_ydl_opts(self) -> Dict[str, Any]:
        """Get base yt-dlp options"""
        opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'ignoreerrors': True,
            'no_color': True,
            # Fix YouTube JavaScript runtime warnings
            'extractor_args': {'youtube': {'player_client': ['default']}},
            # Prevent .meta file downloads
            'writethumbnail': False,
            'writeinfojson': False,
            'writedescription': False,
            'writeannotations': False,
            'writesubtitles': False,
        }
        
        # Add cookies if configured
        if self.config.cookies_file:
            opts['cookiefile'] = self.config.cookies_file
        
        # Add proxy if configured
        if self.config.proxies:
            opts['proxy'] = self.config.proxies[0]
        
        # Add timeout
        if self.config.download_timeout_seconds:
            opts['socket_timeout'] = self.config.download_timeout_seconds
        
        return opts
    
    def get_playlist_info(self, url: str) -> Optional[Dict]:
        """Get playlist information"""
        try:
            ydl_opts = self.get_base_ydl_opts()
            ydl_opts['extract_flat'] = 'in_playlist'
            # Suppress output when fetching playlist info
            ydl_opts['quiet'] = True
            ydl_opts['no_warnings'] = True
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        
        except Exception as e:
            console.print(f"[red]Error fetching playlist info: {e}[/red]")
            return None
    
    def calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return None
    
    def record_success(self, item: DownloadItem, start_time: datetime):
        """Record successful download"""
        end_time = datetime.now()
        item.status = DownloadStatus.COMPLETED.value
        item.download_completed_at = end_time.isoformat()
        item.download_duration_seconds = (end_time - start_time).total_seconds()
        
        if self.stats_manager:
            self.stats_manager.record_download(
                True, 
                item.download_duration_seconds,
                item.file_size_bytes or 0
            )
        
        # Send notification
        if self.notification_manager and self.notification_manager.has_any_notifier():
            file_size_mb = (item.file_size_bytes or 0) / (1024 * 1024)
            self.notification_manager.notify_download_complete(
                item.title,
                file_size_mb,
                item.download_duration_seconds
            )
    
    def record_failure(self, item: DownloadItem, error: str, start_time: datetime):
        """Record failed download"""
        end_time = datetime.now()
        item.status = DownloadStatus.FAILED.value
        item.error = error
        item.download_completed_at = end_time.isoformat()
        item.download_duration_seconds = (end_time - start_time).total_seconds()
        
        if self.stats_manager:
            self.stats_manager.record_download(
                False,
                item.download_duration_seconds,
                0
            )
        
        # Send error notification
        if self.notification_manager and self.notification_manager.has_any_notifier():
            self.notification_manager.notify_error(
                "Download Failed",
                error,
                f"Video: {item.title}"
            )
    
    def check_alerts(self, file_size_bytes: int):
        """Check and send alerts for thresholds"""
        if not self.stats_manager:
            return
        
        triggered = self.stats_manager.check_alert_threshold(file_size_bytes)
        
        for threshold_bytes in triggered:
            threshold_mb = threshold_bytes / (1024 * 1024)
            console.print(f"\n[yellow]⚠ Alert: Downloaded {threshold_mb:.0f} MB today![/yellow]")
            
            if self.notification_manager and self.notification_manager.has_any_notifier():
                stats = self.stats_manager.get_today_stats()
                total_mb = stats.total_file_size_bytes / (1024 * 1024)
                self.notification_manager.notify_size_threshold(int(threshold_mb), total_mb)
    
    @abstractmethod
    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0) -> DownloadItem:
        """Download a single item - must be implemented by subclasses"""
        pass
