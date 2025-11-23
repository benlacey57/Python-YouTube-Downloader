"""Playlist downloader orchestrator"""
from typing import Optional
import time
import random
from rich.console import Console
from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live # <-- New Import

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


# --- NEW STATUS PANEL CLASS ---
class StatusPanel:
    """Manages a persistent status panel for the download process."""
    def __init__(self, queue: Queue, download_all: bool, has_proxies: bool, rotation_enabled: bool, current_proxy: Optional[str] = None):
        self.queue = queue
        self.download_all = download_all
        self.config_manager = ConfigManager()
        self.status_line = "[bold yellow]Initializing...[/bold yellow]"
        self.has_proxies = has_proxies
        self.rotation_enabled = rotation_enabled
        self.current_proxy = current_proxy

    def _get_proxy_info(self):
        """Generates the proxy information string."""
        if self.has_proxies:
            if self.rotation_enabled:
                freq = self.config_manager.config.proxy_rotation_frequency
                return f"[cyan]Proxy Rotation:[/cyan] Enabled (every {freq} downloads)"
            elif self.current_proxy:
                return f"[cyan]Proxy:[/cyan] {self.current_proxy}"
            else:
                 return f"[cyan]Proxy:[/cyan] {self.config_manager.config.proxies[0]}" # Fallback to first if fixed mode
        else:
            return "[yellow]⚠ No proxies configured[/yellow]"
    
    def update_status(self, status: str):
        """Updates the dynamic status line."""
        self.status_line = status

    def __rich__(self) -> Panel:
        """Renders the full panel for rich.live."""
        mode_info = "[yellow]Mode: Download All (ignoring past logs)[/yellow]" if self.download_all else "[cyan]Mode: Pending items only[/cyan]"
        proxy_info = self._get_proxy_info()
        
        header_content = (
            f"[bold cyan]Downloading:[/bold cyan] {self.queue.playlist_title}\n"
            f"[cyan]Format:[/cyan] {self.queue.format_type} | "
            f"[cyan]Quality:[/cyan] {self.queue.quality} | "
            f"[cyan]Storage:[/cyan] {self.queue.storage_provider}\n"
            f"{proxy_info}\n"
            f"{mode_info}\n"
            f"--- [bold white]Current Status:[/bold white] {self.status_line}"
        )
        
        shortcuts = "[bold yellow]Shortcuts:[/bold yellow] [bold]P[/bold] Pause/Resume | [bold]Q[/bold] Quit/Cancel"
        
        # Using a table to combine the header and shortcuts into one panel
        table = Table.grid(padding=(0, 0))
        table.add_row(header_content)
        table.add_row("-" * 80)
        table.add_row(shortcuts)
        
        return Panel(table, border_style="cyan")
# --- END NEW STATUS PANEL CLASS ---


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
        
        if has_proxies and not rotation_enabled:
            current_proxy = config_manager.config.proxies[0]
        
        # Start keyboard listener globally
        keyboard_handler.start_listening()
        
        # Initialize StatusPanel
        status_panel = StatusPanel(
            queue, 
            download_all, 
            has_proxies, 
            rotation_enabled, 
            current_proxy
        )
        
        # Use rich.live to keep the status panel persistent at the top
        with Live(status_panel, screen=False, refresh_per_second=4, console=console) as live:
            try:
                # --- Simulated Playlist Fetching Status ---
                # This is where the *actual* playlist fetching would happen 
                # in a different class, but we'll show the status update here.
                status_panel.update_status("[bold blue]Fetching playlist items...[/bold blue]")
                # Simulate a delay for the fetching process
                time.sleep(random.uniform(1.0, 2.5)) 
                
                items = queue_manager.get_queue_items(queue.id)
                
                # Filter by download order
                status_panel.update_status("[bold blue]Sorting items by download order...[/bold blue]")
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
                    status_panel.update_status(f"[bold yellow]Redownloading all {len(pending_items)} items...[/bold yellow]")
                else:
                    # Only pending items
                    pending_items = [
                        item for item in items
                        if item.status == DownloadStatus.PENDING.value
                    ]
                
                if not pending_items:
                    status_panel.update_status("[bold yellow]No items to download[/bold yellow]")
                    live.stop() # Stop the live panel
                    console.print("\n[yellow]No items to download[/yellow]")
                    return
                
                # --- DOWNLOAD PROGRESS START ---
                # Create a single full-width progress bar, which appears *below* the StatusPanel
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
                    
                    console.print()  # Add spacing after the live panel
                    
                    for idx, item in enumerate(pending_items, 1):
                        # Check for cancellation
                        if keyboard_handler.is_cancelled():
                            status_panel.update_status("[bold red]Download cancelled by user[/bold red]")
                            live.stop() # Stop the live panel
                            console.print("\n[yellow]Download cancelled by user[/yellow]")
                            # Record interruption for resume
                            queue_manager.record_queue_interruption(queue.id)
                            break
                        
                        # Check for pause
                        while keyboard_handler.is_paused() and not keyboard_handler.is_cancelled():
                            status_panel.update_status("[bold magenta]Paused (Press P to resume)...[/bold magenta]")
                            time.sleep(0.5)
                        
                        # Resume status update if paused
                        if not keyboard_handler.is_paused():
                            status_panel.update_status(f"[bold cyan]Processing Item {idx}/{len(pending_items)}: {item.title[:60]}...[/bold cyan]")
                        
                        # Handle proxy rotation/selection
                        proxy_display = ""
                        if rotation_enabled:
                            # Rotate proxy based on frequency
                            proxy_index = (download_count // config_manager.config.proxy_rotation_frequency) % len(config_manager.config.proxies)
                            current_proxy = config_manager.config.proxies[proxy_index]
                            download_count += 1
                            proxy_display = f" [blue]| Proxy:[/blue] {current_proxy}"
                            status_panel.current_proxy = current_proxy # Update panel proxy display
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
                                status_panel.update_status(f"[bold dim]Waiting {wait_time:.1f}s between items...[/bold dim]")
                                console.print(f"  [dim]Waiting {wait_time:.1f}s...[/dim]")
                                time.sleep(wait_time)
                            console.print()  # Add spacing between items
                
                # Mark queue as completed if not cancelled
                if not keyboard_handler.is_cancelled():
                    status_panel.update_status(f"[bold green]Queue completed: {queue.playlist_title}[/bold green]")
                    
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
                    
                    # Stop the live panel before final print
                    live.stop()
                    console.print(f"\n[bold green]✓ Queue completed: {queue.playlist_title}[/bold green]")
            
            finally:
                # Ensure the keyboard listener and live panel are stopped on exit/error
                live.stop() 
                keyboard_handler.stop_listening()
                keyboard_handler.reset()
                        
