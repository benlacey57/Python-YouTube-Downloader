"""Live stream downloader"""
import yt_dlp
from pathlib import Path
from datetime import datetime
import logging # <-- ADDED IMPORT
from typing import Optional # <-- ADDED IMPORT

from downloaders.base import BaseDownloader
from managers.config_manager import ConfigManager
from managers.stats_manager import StatsManager
from managers.notification_manager import NotificationManager
from models.download_item import DownloadItem # <-- ADDED
from models.queue import Queue # <-- ADDED
from enums import DownloadStatus # <-- ADDED
from utils.file_renamer import FileRenamer # <-- ADDED
from utils.metadata_handler import MetadataHandler
from rich.console import Console

console = Console()
logger = logging.getLogger('LiveStreamDownloader') # <-- ADDED LOGGER


class LiveStreamDownloader(BaseDownloader):
    """Handles live stream recording"""
    
    def __init__(self):
        # Get managers internally
        config_manager = ConfigManager()
        stats_manager = StatsManager()
        notification_manager = NotificationManager(config_manager.config)
        
        # Initialize base
        super().__init__(
            config_manager.config,
            stats_manager,
            notification_manager
        )
        
        self.live_stream_recorder = LiveStreamRecorder()
    
    def is_live_stream(self, info: dict) -> bool:
        """Check if content is a live stream"""
        return self.live_stream_recorder.is_live_stream(info)

    def _log_error(self, e: Exception, filepath: Optional[str] = None):
        """Helper to log errors to the file."""
        context = f"(File: {filepath})" if filepath else "(No file path found)"
        logger.error(f"Error in LiveStreamDownloader {context}: {e}", exc_info=True)
    
    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0, proxy: str = None) -> DownloadItem:
        """Download/record a live stream"""
        from utils.keyboard_handler import keyboard_handler
        if keyboard_handler.is_skip_requested():
            console.print(f"[cyan]Skipping: {item.title}[/cyan]")
            item.status = DownloadStatus.PENDING.value
            item.error = "Skipped by user"
            return item
        
        self.rate_limiter.wait_if_needed()
        
        item.status = DownloadStatus.DOWNLOADING.value
        item.download_started_at = datetime.now().isoformat()
        start_time = datetime.now()
        
        if queue.filename_template:
            base_filename = FileRenamer.apply_template(
                queue.filename_template,
                item.title,
                item.uploader or "Unknown",
                item.upload_date or "Unknown",
                index,
                queue.playlist_title,
                item.video_id or "unknown",
                normalize=self.config.normalize_filenames
            )
        else:
            base_filename = FileRenamer.sanitize_filename(
                item.title,
                normalize=self.config.normalize_filenames
            )
        
        ydl_opts = self.get_base_ydl_opts(proxy=proxy)
        ydl_opts['outtmpl'] = f'{queue.output_dir}/{base_filename}.%(ext)s'
        
        # Get live stream recording options
        stream_opts = self.live_stream_recorder.get_recording_opts(
            wait_for_stream=self.config.wait_for_scheduled_streams,
            max_wait_minutes=self.config.max_stream_wait_minutes
        )
        ydl_opts.update(stream_opts)
        
        filename = None # Initialize filename
        
        try:
            console.print(f"[yellow]Recording live stream: {item.title}[/yellow]")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=False)
                
                if not item.upload_date:
                    item.upload_date = info.get('upload_date')
                if not item.uploader:
                    item.uploader = info.get('uploader')
                if not item.video_id:
                    item.video_id = info.get('id')
                
                info = ydl.extract_info(item.url, download=True)
                filename = ydl.prepare_filename(info)
                
                item.file_path = str(filename)
                
                if Path(filename).exists():
                    item.file_size_bytes = Path(filename).stat().st_size
                
                item.file_hash = self.calculate_file_hash(filename)
                
                self.record_success(item, start_time)
                self.check_alerts(item.file_size_bytes or 0)
                
                console.print(f"[green]✓ Live stream recorded: {item.title}[/green]")
        
        except Exception as e:
            error_msg = str(e)
            
            # Log the full exception, including the file path
            self._log_error(e, filepath=filename)

            self.record_failure(item, error_msg, start_time)
            console.print(f"[red]✗ Failed to record live stream: {error_msg}[/red]")
        
        return item
        
