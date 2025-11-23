"""Playlist downloader orchestrator"""
from typing import Optional
import time
import random
from rich.console import Console
from rich.progress import Progress, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live          # <-- For persistent status panel
import yt_dlp
import logging                      # <-- For centralized error logging

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

# --- GLOBAL ERROR LOGGING SETUP ---
# Configure logging to write to errors.log file
logging.basicConfig(
    filename='errors.log', 
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)
# -----------------------------------

# --- STATUS PANEL CLASS (FOR PERSISTENT DISPLAY) ---
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
                 # Fallback to first if fixed mode
                 proxy = self.config_manager.config.proxies[0] if self.config_manager.config.proxies else "N/A"
                 return f"[cyan]Proxy:[/cyan] {proxy}" 
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
        
        # This is the permanently visible panel row for shortcuts
        shortcuts = "[bold yellow]Shortcuts:[/bold yellow] [bold]P[/bold] Pause/Resume | [bold]Q[/bold] Quit/Cancel | [bold]S[/bold] Skip Current"
        
        # Using a table to combine the header and shortcuts into one panel
        table = Table.grid(padding=(0, 0))
        table.add_row(header_content)
        table.add_row("-" * 80)
        table.add_row(shortcuts)
        
        return Panel(table, border_style="cyan")
# -------------------------------------------------------------

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
    
    def _log_error(self, e: Exception, context: str = ""):
        """Helper to log errors to the file."""
        logger.error(f"Error in PlaylistDownloader (Context: {context}): {e}", exc_info=True)

    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0, proxy: str = None) -> DownloadItem:
        """
        Download a single item using the appropriate downloader
        This method delegates to specialized downloaders
        """
        # Check if it's a live stream first
        try:
            ydl_opts = self.get_base_ydl_opts()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(item.url, download=False)
                except Exception as e:
                    # Log failure during info extraction but try proceeding with normal download
                    self._log_error(e, context=f"Info extraction for {item.title}")
                    return self.video_downloader.download_item(item, queue, index, proxy=proxy)

                if self.livestream_downloader.is_live_stream(info):
                    if self.config.auto_record_live_streams:
                        return self.livestream_downloader.download_item(item, queue, index, proxy=proxy)
                    else:
                        console.print(f"[yellow]Skipping live stream (auto-record disabled): {item.title}[/yellow]")
                        item.status = DownloadStatus.FAILED.value
                        item.error = "Live stream - auto-record disabled"
                        return item
        except Exception as e:
            # Catch errors in the live stream check itself (e.g. yt_dlp import fails or network issues)
            self._log_error(e, context="General Live Stream Check")
            # Proceed with normal download logic if the check fails
            
        # Use appropriate downloader based on format
        if queue.format_type == "audio":
            return self.audio_downloader.download_item(item, queue, index, proxy=proxy)
        else:
            return self.video_downloader.download_item(item, queue, index, proxy=proxy)

    def download_queue(self, queue: Queue, queue_manager: QueueManager, download_all: bool = False):
        """Download all items in a queue"""
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
                items = []
                pending_items = []
                
                # --- SETUP PHASE WITH TRANSIENT PROGRESS BAR ---
                # This progress bar handles the initial fetching/sorting steps.
                with Progress(
                    BarColumn(bar_width=None),
                    TaskProgressColumn(),
                    console=console,
                    expand=True,
                    transient=True # IMPORTANT: This bar disappears once the setup is done
                ) as setup_progress:
                    setup_task = setup_progress.add_task("[bold blue]Initializing Queue Setup...", total=3)
                    
                    # 1. Fetch items from DB
                    status_panel.update_status("[bold blue]Fetching items from database...[/bold blue]")
                    console.print(f"[dim]Loading items for queue ID: {queue.id}[/dim]")
                    items = queue_manager.get_queue_items(queue.id)
                    setup_progress.update(setup_task, advance=1, description="[bold green]Items fetched[/bold green]")
                    
                    # 2. Sort items
                    status_panel.update_status("[bold blue]Sorting items by download order...[/bold blue]")
                    if queue.download_order == 'newest_first':
                        items = sorted(items, key=lambda x: x.upload_date or '', reverse=True)
                    elif queue.download_order == 'oldest_first':
                        items = sorted(items, key=lambda x: x.upload_date or '')
                    setup_progress.update(setup_task, advance=1, description="[bold green]Items sorted[/bold green]")
                    
                    # 3. Filter/reset items based on download_all flag
                    status_panel.update_status("[bold blue]Checking download mode and filtering pending items...[/bold blue]")
                    if download_all:
                        pending_items = items
                        # Reset all items to pending status for redownload
                        for item in pending_items:
                            item.status = DownloadStatus.PENDING.value
                            item.error = None
                            queue_manager.update_item(item)
                        status_panel.update_status(f"[bold yellow]Redownloading all {len(pending_items)} items...[/bold yellow]")
                    else:
                        pending_items = [
                            item for item in items
                            if item.status == DownloadStatus.PENDING.value
                        ]
                    
                    setup_progress.update(setup_task, advance=1, description="[bold green]Queue setup complete[/bold green]")
                # --- END SETUP PHASE ---
                
                if not pending_items:
                    status_panel.update_status("[bold yellow]No items to download[/bold yellow]")
                    time.sleep(1)
                    live.stop() 
                    console.print("\n[yellow]No items to download[/yellow]")
                    return
                
                # --- DOWNLOAD PROGRESS START (MAIN LOOP) ---
                status_panel.update_status(f"[bold green]Starting download of {len(pending_items)} items...[/bold green]")
                
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
                    
                    console.print() 
                    
                    for idx, item in enumerate(pending_items, 1):
                        # ... rest of the download loop logic ...
                        
                        # ...
                        progress.update(overall_task, advance=1)
                        
                        # Add random wait time between downloads if no proxies configured
                        if idx < len(pending_items) and not has_proxies:
                            wait_time = random.uniform(
                                config_manager.config.min_delay_seconds,
                                config_manager.config.max_delay_seconds
                            )
                            status_panel.update_status(f"[bold dim]Waiting {wait_time:.1f}s between items...[/bold dim]")
                            console.print(f"  [dim]Waiting {wait_time:.1f}s...[/dim]")
                            time.sleep(wait_time)
                            console.print()
                
                # Mark queue as completed if not cancelled
                if not keyboard_handler.is_cancelled():
                    # ... completion logic ...
            
            except Exception as e:
                # Catch and log fatal errors in the orchestration logic
                self._log_error(e, context="download_queue fatal error")
                status_panel.update_status("[bold red]FATAL ERROR: See errors.log[/bold red]")
                time.sleep(1)
                live.stop()
                console.print(f"\n[bold red]FATAL ERROR: An unexpected error occurred. See errors.log for details.[/bold red]")
                
            finally:
                keyboard_handler.stop_listening()
                keyboard_handler.reset()
                
