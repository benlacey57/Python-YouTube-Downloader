"""Video downloader"""
import yt_dlp
from pathlib import Path
from datetime import datetime
import logging # <-- ADDED IMPORT
from typing import Optional # <-- ADDED IMPORT

from downloaders.base import BaseDownloader
from managers.config_manager import ConfigManager
# ... other imports
from utils.metadata_handler import MetadataHandler
from rich.console import Console

console = Console()
logger = logging.getLogger('VideoDownloader') # <-- ADDED LOGGER

class VideoDownloader(BaseDownloader):
    """Handles video downloads"""
    
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

    def _log_error(self, e: Exception, filepath: Optional[str] = None):
        """Helper to log errors to the file."""
        context = f"(File: {filepath})" if filepath else "(No file path found)"
        logger.error(f"Error in VideoDownloader {context}: {e}", exc_info=True)
    
    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0, proxy: str = None) -> DownloadItem:
        """Download a video item"""
        # Check for skip request
        from utils.keyboard_handler import keyboard_handler
        if keyboard_handler.is_skip_requested():
            console.print(f"[cyan]Skipping: {item.title}[/cyan]")
            item.status = DownloadStatus.PENDING.value
            item.error = "Skipped by user"
            return item
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        item.status = DownloadStatus.DOWNLOADING.value
        item.download_started_at = datetime.now().isoformat()
        start_time = datetime.now()
        
        # Apply filename template
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
        
        # Add progress hook
        def progress_hook(d):
            if keyboard_handler.is_skip_requested():
                raise Exception("Download skipped by user")
        
        ydl_opts['progress_hooks'] = [progress_hook]
        
        # Set video quality
        quality = queue.storage_video_quality or queue.quality
        
        if quality == 'best':
            format_str = 'bestvideo+bestaudio/best'
        elif quality == 'worst':
            format_str = 'worstvideo+worstaudio/worst'
        else:
            height = quality.replace('p', '')
            format_str = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
        
        ydl_opts['format'] = format_str
        ydl_opts['merge_output_format'] = 'mp4'
        
        filename = None # Initialize filename
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get info
                info = ydl.extract_info(item.url, download=False)
                
                # Update metadata
                if not item.upload_date:
                    item.upload_date = info.get('upload_date')
                if not item.uploader:
                    item.uploader = info.get('uploader')
                if not item.video_id:
                    item.video_id = info.get('id')
                
                # Download
                info = ydl.extract_info(item.url, download=True)
                filename = ydl.prepare_filename(info)
                
                item.file_path = str(filename)
                
                # Get file size
                if Path(filename).exists():
                    item.file_size_bytes = Path(filename).stat().st_size
                    
                    # Set metadata
                    metadata = MetadataHandler.extract_metadata(
                        info, index, queue.playlist_title
                    )
                    MetadataHandler.set_video_metadata(filename, metadata)
                
                item.file_hash = self.calculate_file_hash(filename)
                
                self.record_success(item, start_time)
                self.check_alerts(item.file_size_bytes or 0)
        
        except Exception as e:
            error_msg = str(e)
            
            # Log the full exception, including the file path
            self._log_error(e, filepath=filename)

            if "skipped by user" in error_msg.lower():
                item.status = DownloadStatus.PENDING.value
                item.error = "Skipped by user"
            else:
                self.record_failure(item, error_msg, start_time)
        
        return item
        
