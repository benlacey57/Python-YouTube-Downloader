"""Playlist downloader orchestrator"""
from typing import Optional
import time
import random
from rich.console import Console
from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

from downloaders.base import BaseDownloader
from downloaders.video import VideoDownloader
from downloaders.audio import AudioDownloader
from downloaders.livestream import LiveStreamDownloader
from managers.config_manager import ConfigManager
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
    
    def __init__(self):
        # Get managers internally
        config_manager = ConfigManager()
        self.stats_manager = StatsManager()
        self.notification_manager = NotificationManager(config_manager.config)
        
        # Initialize base with config
        super().__init__(
            config_manager.config,
            self.stats_manager,
            self.notification_manager
        )
        
        # Initialize specialized downloaders
        self.video_downloader = VideoDownloader()
        self.audio_downloader = AudioDownloader()
        self.livestream_downloader = LiveStreamDownloader()
    
    def _print_stats(self, stats: dict):
        """Print download statistics"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")
        
        table.add_row("Total:", f"{stats['total']}")
        table.add_row("Completed:", f"[green]{stats['completed']}[/green]")
        table.add_row("Failed:", f"[red]{stats['failed']}[/red]")
        table.add_row("Pending:", f"[yellow]{stats['pending']}[/yellow]")
        
        panel = Panel(table, title="[bold]Progress[/bold]", border_style="cyan", width=40)
        console.print(panel)
    
    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0, proxy: str = None) -> DownloadItem:
        """
        Download a single item using the appropriate downloader
        This method delegates to specialized downloaders
        
        Args:
            item: Download item to process
            queue: Queue configuration
            index: Item index in queue
            proxy: Optional specific proxy to use for this download
        """
        # Check if it's a live stream first
        try:
            import yt_dlp
            ydl_opts = self.get_base_ydl_opts()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=False)
                
                if self.livestream_downloader.is_live_stream(info):
                    if self.config.auto_record_live_streams:
                        return self.livestream_downloader.download_item(item, queue, index, proxy=proxy)
                    else:
                        console.print(f"[yellow]Skipping live stream (auto-record disabled): {item.title}[/yellow]")
                        item.status = DownloadStatus.FAILED.value
                        item.error = "Live stream - auto-record disabled"
                        return item
        except:
            pass  # If we can't check, proceed with normal download
        
        # Use appropriate downloader based on format
        if queue.format_type == "audio":
            return self.audio_downloader.download_item(item, queue, index, proxy=proxy)
        else:
            return self.video_downloader.download_item(item, queue, index, proxy=proxy)
    
    def download_queue(self, queue: Queue, queue_manager: QueueManager, download_all: bool = False):
        """Download all items in a queue
        
        Args:
            queue: Queue to download
            queue_manager: Queue manager instance
            download_all: If True, download all items regardless of status
        """
        console.clear()
        
        # Get config for proxy settings
        config_manager = ConfigManager()
        has_proxies = config_manager.config.proxies and len(config_manager.config.proxies) > 0
        rotation_enabled = config_manager.config.proxy_rotation_enabled and has_proxies
        current_proxy = None
        download_count = 0
        
        # Prepare proxy info for header
        proxy_info = ""
        if has_proxies:
            if rotation_enabled:
                proxy_info = f"[cyan]Proxy Rotation:[/cyan] Enabled (every {config_manager.config.proxy_rotation_frequency} downloads)"
            else:
                # Use first proxy if rotation disabled
                current_proxy = config_manager.config.proxies[0]
                proxy_info = f"[cyan]Proxy:[/cyan] {current_proxy}"
        else:
            proxy_info = "[yellow]⚠ No proxies configured[/yellow]"
        
        mode_info = "[yellow]Mode: Download All (ignoring past logs)[/yellow]" if download_all else "[cyan]Mode: Pending items only[/cyan]"
        
        header = Panel(
            f"[bold cyan]Downloading:[/bold cyan] {queue.playlist_title}\n"
            f"[cyan]Format:[/cyan] {queue.format_type} | "
            f"[cyan]Quality:[/cyan] {queue.quality} | "
            f"[cyan]Storage:[/cyan] {queue.storage_provider}\n"
            f"{proxy_info}\n"
            f"{mode_info}",
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
            
            # Filter items based on download_all flag
            if download_all:
                # Reset all items to pending for redownload
                pending_items = items
                for item in pending_items:
                    item.status = DownloadStatus.PENDING.value
                    item.error = None
                    queue_manager.update_item(item)
                console.print(f"[yellow]Redownloading all {len(pending_items)} items...[/yellow]\n")
            else:
                # Only pending items
                pending_items = [
                    item for item in items
                    if item.status == DownloadStatus.PENDING.value
                ]
            
            if not pending_items:
                console.print("[yellow]No items to download[/yellow]")
                return
            
            # Create a single full-width progress bar
            with Progress(
                BarColumn(bar_width=None),  # Full width
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
                expand=True
            ) as progress:
                
                overall_task = progress.add_task(
                    f"[cyan]Overall Progress",
                    total=len(pending_items)
                )
                
                console.print()  # Add spacing
                
                for idx, item in enumerate(pending_items, 1):
                    # Check for cancellation
                    if keyboard_handler.is_cancelled():
                        console.print("\n[yellow]Download cancelled by user[/yellow]")
                        # Record interruption for resume
                        queue_manager.record_queue_interruption(queue.id)
                        break
                    
                    # Check for pause
                    while keyboard_handler.is_paused() and not keyboard_handler.is_cancelled():
                        time.sleep(0.5)
                    
                    # Handle proxy rotation/selection
                    proxy_display = ""
                    if rotation_enabled:
                        # Rotate proxy based on frequency
                        proxy_index = (download_count // config_manager.config.proxy_rotation_frequency) % len(config_manager.config.proxies)
                        current_proxy = config_manager.config.proxies[proxy_index]
                        download_count += 1
                        proxy_display = f" [blue]| Proxy:[/blue] {current_proxy}"
                    elif has_proxies and current_proxy:
                        # Fixed proxy mode
                        proxy_display = f" [blue]| Proxy:[/blue] {current_proxy}"
                    
                    # Show current item on one line with proxy
                    console.print(f"[cyan]► [{idx}/{len(pending_items)}][/cyan] {item.title[:80]}{proxy_display}")
                    
                    # Download the item (pass proxy if rotation enabled)
                    item = self.download_item(item, queue, idx, proxy=current_proxy)
                    queue_manager.update_item(item)
                    
                    # Show result with file size if available
                    if item.status == DownloadStatus.COMPLETED.value:
                        size_str = ""
                        if item.file_size_bytes:
                            size_mb = item.file_size_bytes / (1024 * 1024)
                            if size_mb >= 1024:
                                size_str = f" ({size_mb/1024:.2f} GB)"
                            else:
                                size_str = f" ({size_mb:.1f} MB)"
                        console.print(f"  [green]✓ Downloaded successfully{size_str}[/green]")
                    elif item.status == DownloadStatus.FAILED.value:
                        console.print(f"  [red]✗ Failed: {item.error}[/red]")
                    
                    progress.update(overall_task, advance=1)
                    
                    # Add random wait time between downloads if no proxies configured
                    if idx < len(pending_items):  # Don't wait after last item
                        if not has_proxies:
                            # Random wait between min and max delay
                            wait_time = random.uniform(
                                config_manager.config.min_delay_seconds,
                                config_manager.config.max_delay_seconds
                            )
                            console.print(f"  [dim]Waiting {wait_time:.1f}s...[/dim]")
                            time.sleep(wait_time)
                        console.print()  # Add spacing between items
            
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
