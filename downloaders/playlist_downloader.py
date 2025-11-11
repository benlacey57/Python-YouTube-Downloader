"""Playlist download operations"""
import shutil
import hashlib
from typing import Optional, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import yt_dlp
except ImportError:
    print("yt-dlp not installed. Please run: pip install yt-dlp")
    exit(1)

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.prompt import Confirm

# Updated imports using absolute paths
from models.download_item import DownloadItem
from models.queue import Queue
from managers.queue_manager import QueueManager
from managers.stats_manager import StatsManager
from managers.proxy_manager import ProxyManager
from notifiers.slack_notifier import SlackNotifier # Assuming you update this to use BaseNotifier
from utils.file_renamer import FileRenamer
from enums import DownloadStatus

console = Console()


class PlaylistDownloader:
    """Handles playlist downloading operations"""

    def __init__(self, config, stats_manager: Optional[StatsManager] = None,
                 slack_notifier: Optional[SlackNotifier] = None):
        self.config = config
        self.stats_manager = stats_manager
        self.slack_notifier = slack_notifier
        self.proxy_manager = ProxyManager(config.proxies)

    def check_ffmpeg(self) -> bool:
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

    def get_base_ydl_opts(self, use_proxy: bool = True) -> Dict:
        """Get base yt-dlp options with authentication and proxy"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,  # Disable yt-dlp's progress bars
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
        ydl_opts = self.get_base_ydl_opts()
        ydl_opts['extract_flat'] = True
    
        # Add more verbose error reporting
        ydl_opts['quiet'] = False
        ydl_opts['no_warnings'] = False

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                console.print("[dim]Extracting playlist information...[/dim]")
                info = ydl.extract_info(url, download=False)
            
                if info:
                    console.print(f"[green]Successfully extracted info for: {info.get('title', 'Unknown')}[/green]")
            
                return info
        except yt_dlp.utils.DownloadError as e:
            console.print(f"[red]Download error: {e}[/red]")
            console.print("[yellow]This might be due to:[/yellow]")
            console.print("  - Age-restricted or private content")
            console.print("  - Geographic restrictions")
            console.print("  - Invalid URL format")
            return None
        except yt_dlp.utils.ExtractorError as e:
            console.print(f"[red]Extractor error: {e}[/red]")
            console.print("[yellow]The URL format might not be supported[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error extracting playlist info: {e}[/red]")
            console.print("[yellow]Try configuring authentication or using a proxy[/yellow]")
            return None    
            
        ydl_opts['extract_flat'] = True
        
    def search_channel_playlists(self, channel_url: str) -> List[Dict]:
        """Search for playlists in a channel"""
        ydl_opts = self.get_base_ydl_opts()
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

    def download_item(self, item: DownloadItem, queue: Queue, index: int = 0) -> DownloadItem:
        """Download a single item"""
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
                item.video_id or "unknown"
            )
        else:
            base_filename = FileRenamer.sanitize_filename(item.title)

        ydl_opts = self.get_base_ydl_opts()
        ydl_opts['outtmpl'] = f'{queue.output_dir}/{base_filename}.%(ext)s'

        if queue.format_type == "audio":
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
            ydl_opts['writethumbnail'] = False
            ydl_opts['keepvideo'] = False
            ydl_opts['prefer_ffmpeg'] = True
        else:
            if queue.quality == 'best':
                format_str = 'bestvideo+bestaudio/best'
            elif queue.quality == 'worst':
                format_str = 'worstvideo+worstaudio/worst'
            else:
                format_str = f'bestvideo[height<={queue.quality.replace("p", "")}]+bestaudio/best[height<={queue.quality.replace("p", "")}]'

            ydl_opts['format'] = format_str
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=True)

                # Update item metadata
                if not item.upload_date:
                    item.upload_date = info.get('upload_date')
                if not item.uploader:
                    item.uploader = info.get('uploader')
                if not item.video_id:
                    item.video_id = info.get('id')

                if queue.format_type == "audio":
                    filename = f"{queue.output_dir}/{base_filename}.mp3"

                    if not Path(filename).exists():
                        possible_files = list(Path(queue.output_dir).glob(f"{base_filename}.*"))
                        if possible_files:
                            filename = str(possible_files[0])
                else:
                    filename = ydl.prepare_filename(info)

                item.file_path = str(filename)

                # Get file size
                if Path(filename).exists():
                    item.file_size_bytes = Path(filename).stat().st_size

                item.file_hash = self._calculate_file_hash(filename)
                item.status = DownloadStatus.COMPLETED.value

                end_time = datetime.now()
                item.download_completed_at = end_time.isoformat()
                item.download_duration_seconds = (end_time - start_time).total_seconds()

                # Record stats and check thresholds
                if self.stats_manager:
                    self.stats_manager.record_download(True, item.download_duration_seconds, item.file_size_bytes or 0)
                    
                    # Check alert thresholds
                    triggered = self.stats_manager.check_alert_threshold(item.file_size_bytes or 0)
                    for threshold_bytes in triggered:
                        threshold_mb = threshold_bytes / (1024 * 1024)
                        console.print(f"\n[yellow]⚠️  Alert: Downloaded {threshold_mb:.0f} MB today![/yellow]")
                        
                        # Send Slack notification
                        if self.slack_notifier and self.slack_notifier.is_configured():
                            stats = self.stats_manager.get_today_stats()
                            total_mb = stats.total_file_size_bytes / (1024 * 1024)
                            self.slack_notifier.notify_size_threshold(int(threshold_mb), total_mb)

        except Exception as e:
            item.status = DownloadStatus.FAILED.value
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

    def download_queue(self, queue: Queue, queue_manager: QueueManager):
        """Download all items in a queue with parallel processing"""
        # Get all items for this queue
        items = queue_manager.get_queue_items(queue.id)

        # Reset stuck items
        stuck_items = [item for item in items if item.status == DownloadStatus.DOWNLOADING.value]
        if stuck_items:
            console.print(f"\n[yellow]Found {len(stuck_items)} items stuck in 'downloading' state[/yellow]")
            console.print("[yellow]Resetting them to 'pending' for retry...[/yellow]\n")
            for item in stuck_items:
                item.status = DownloadStatus.PENDING.value
                queue_manager.update_item(item)

        # Get pending items
        items = queue_manager.get_queue_items(queue.id)
        pending_items = [
            item for item in items
            if item.status in (DownloadStatus.PENDING.value, DownloadStatus.FAILED.value)
        ]

        if not pending_items:
            console.print("[green]All items already downloaded![/green]")
            return

        # Sort items based on download order
        pending_items = self._sort_items(pending_items, queue.download_order)

        # Display info panel
        info_panel = Panel(
            f"[cyan]Playlist:[/cyan] {queue.playlist_title}\n"
            f"[cyan]Items:[/cyan] {len(pending_items)}\n"
            f"[cyan]Workers:[/cyan] {self.config.max_workers}\n"
            f"[cyan]Order:[/cyan] {queue.download_order}\n"
            f"[cyan]Format:[/cyan] {queue.format_type}\n"
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
                        queue,
                        idx
                    )
                    future_to_item[future] = item

                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        updated_item = future.result()

                        # Update item in database
                        queue_manager.update_item(updated_item)

                        duration_str = self._format_duration(updated_item.download_duration_seconds)
                        size_str = self._format_size(updated_item.file_size_bytes)

                        if updated_item.status == DownloadStatus.COMPLETED.value:
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

        # Mark queue as completed
        queue.completed_at = datetime.now().isoformat()
        queue_manager.update_queue(queue)

        # Record queue completion
        if self.stats_manager:
            self.stats_manager.record_queue_completed()

        # Get final item stats
        items = queue_manager.get_queue_items(queue.id)
        self._print_summary(items, queue, queue_start_time)
        self._check_duplicates(items)

        # Send Slack notification
        if self.slack_notifier and self.slack_notifier.is_configured():
            completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
            failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
            total_duration = (datetime.now() - queue_start_time).total_seconds()

            self.slack_notifier.notify_queue_completed(
                queue.playlist_title,
                completed,
                failed,
                len(items),
                self._format_duration(total_duration)
            )

    def _sort_items(self, items: List[DownloadItem], order: str) -> List[DownloadItem]:
        """Sort items based on download order"""
        if order == "newest_first":
            return list(reversed(items))
        elif order == "oldest_first":
            return items
        else:
            return items

    def _print_summary(self, items: List[DownloadItem], queue: Queue, queue_start_time: datetime):
        """Print download summary with timing information"""
        from rich.table import Table

        completed = [item for item in items if item.status == DownloadStatus.COMPLETED.value]
        failed = [item for item in items if item.status == DownloadStatus.FAILED.value]

        total_time = sum(
            item.download_duration_seconds
            for item in items
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
        table.add_row("Total", str(len(items)),
                     f"Time: {self._format_duration(total_time)}")
        table.add_row("Size", "", f"{self._format_size(total_size)}")
        table.add_row("Queue Duration", "", f"{self._format_duration(queue_duration)}")

        console.print("\n")
        console.print(table)

        # Show slowest downloads
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

    def _check_duplicates(self, items: List[DownloadItem]):
        """Check for duplicate files by hash"""
        hash_to_items = {}

        for item in items:
            if item.status == DownloadStatus.COMPLETED.value and item.file_hash:
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
