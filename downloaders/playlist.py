"""Playlist downloader orchestrator"""
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel

from downloaders.base import BaseDownloader
from downloaders.video import VideoDownloader
from downloaders.audio import AudioDownloader
from downloaders.livestream import LiveStreamDownloader
from managers.config_manager import AppConfig
from managers.stats_manager import StatsManager
from managers.queue_manager import QueueManager
from managers.notification_manager import NotificationManager
from models.queue import Queue
from models.download_item import DownloadItem
from enums import DownloadStatus
from utils.keyboard_handler import keyboard_handler

console = Console()


class PlaylistDownloader(BaseDownloader):
    """Orchestrates playlist downloads using specialized downloaders"""
    
    def __init__(self, config: AppConfig, stats_manager: StatsManager = None,
                 notification_manager: NotificationManager = None):
        super().__init__(config, stats_manager, notification_manager)
        
        # Initialize specialized downloaders
        self.video_downloader = VideoDownloader(config, stats_manager, notification_manager)
        self.audio_downloader = AudioDownloader(config, stats_manager, notification_manager)
        self.livestream_downloader = LiveStreamDownloader(config, stats_manager, notification_manager)
    
    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0) -> DownloadItem:
        """
        Download a single item using the appropriate downloader
        This method delegates to specialized downloaders
        """
        # Check if it's a live stream first
        try:
            import yt_dlp
            ydl_opts = self.get_base_ydl_opts()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=False)
                
                if self.livestream_downloader.is_live_stream(info):
                    if self.config.auto_record_live_streams:
                        return self.livestream_downloader.download_item(item, queue, index)
                    else:
                        console.print(f"[yellow]Skipping live stream (auto-record disabled): {item.title}[/yellow]")
                        item.status = DownloadStatus.FAILED.value
                        item.error = "Live stream - auto-record disabled"
                        return item
        except:
            pass  # If we can't check, proceed with normal download
        
        # Use appropriate downloader based on format
        if queue.format_type == "audio":
            return self.audio_downloader.download_item(item, queue, index)
        else:
            return self.video_downloader.download_item(item, queue, index)
    
    def download_queue(self, queue: Queue, queue_manager: QueueManager):
        """Download all items in a queue"""
        console.clear()
        
        header = Panel(
            f"[bold cyan]Downloading:[/bold cyan] {queue.playlist_title}\n"
            f"[cyan]Format:[/cyan] {queue.format_type} | "
            f"[cyan]Quality:[/cyan] {queue.quality} | "
            f"[cyan]Storage:[/cyan] {queue.storage_provider}",
            border_style="cyan"
        )
        console.print(header)
        
        # Start keyboard listener
        keyboard_handler.start_listening()
        
        try:
            items = queue_manager.get_queue_items(queue.id)
            
            # Filter by download order
            if queue.download_order == 'newest_first':
                items = sorted(items, key=lambda x: x.upload_date or '', reverse=True)
            elif queue.download_order == 'oldest_first':
                items = sorted(items, key=lambda x: x.upload_date or '')
            
            # Filter pending items
            pending_items = [
                item for item in items
                if item.status == DownloadStatus.PENDING.value
            ]
            
            if not pending_items:
                console.print("[yellow]No pending items to download[/yellow]")
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task(
                    "Downloading...",
                    total=len(pending_items)
                )
                
                for idx, item in enumerate(pending_items, 1):
                    # Check for cancellation
                    if keyboard_handler.is_cancelled():
                        console.print("\n[yellow]Download cancelled by user[/yellow]")
                        # Record interruption for resume
                        queue_manager.record_queue_interruption(queue.id)
                        break
                    
                    # Check for pause
                    while keyboard_handler.is_paused() and not keyboard_handler.is_cancelled():
                        import time
                        time.sleep(0.5)
                    
                    progress.console.print(f"\n[cyan][{idx}/{len(pending_items)}] {item.title}[/cyan]")
                    
                    # Download the item
                    item = self.download_item(item, queue, idx)
                    queue_manager.update_item(item)
                    
                    if item.status == DownloadStatus.COMPLETED.value:
                        progress.console.print(f"[green]✓ Downloaded successfully[/green]")
                    elif item.status == DownloadStatus.FAILED.value:
                        progress.console.print(f"[red]✗ Failed: {item.error}[/red]")
                    
                    progress.update(task, advance=1)
            
            # Mark queue as completed if not cancelled
            if not keyboard_handler.is_cancelled():
                from datetime import datetime
                queue.completed_at = datetime.now().isoformat()
                queue_manager.update_queue(queue)
                
                # Clear resume data
                queue_manager.clear_queue_resume(queue.id)
                
                if self.stats_manager:
                    self.stats_manager.record_queue_completed()
                
                # Send completion notification
                if self.notification_manager and self.notification_manager.has_any_notifier():
                    completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
                    self.notification_manager.notify_queue_completed(
                        queue.playlist_title,
                        completed,
                        len(items)
                    )
                
                console.print(f"\n[bold green]✓ Queue completed: {queue.playlist_title}[/bold green]")
        
        finally:
            keyboard_handler.stop_listening()
            keyboard_handler.reset()
