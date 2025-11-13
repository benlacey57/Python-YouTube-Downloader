"""Queue builder wizard"""
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from datetime import datetime
from pathlib import Path

from managers.config_manager import ConfigManager
from managers.queue_manager import QueueManager
from models.queue import Queue
from models.download_item import DownloadItem
from downloaders.playlist import PlaylistDownloader

console = Console()


class QueueBuilder:
    """Build download queues interactively"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.queue_manager = QueueManager()
        self.downloader = PlaylistDownloader()
    
    def build_queue(self):
        """Build a new download queue"""
        console.clear()
        
        header = Panel(
            "[bold cyan]Create Download Queue[/bold cyan]\n"
            "Add a new playlist to download",
            border_style="cyan"
        )
        console.print(header)
        
        # Get playlist URL
        console.print("\n[yellow]Step 1: Playlist Information[/yellow]")
        playlist_url = Prompt.ask("Enter playlist URL")
        
        if not playlist_url:
            console.print("[red]URL is required[/red]")
            input("\nPress Enter to continue...")
            return
        
        # Get playlist info
        console.print("\n[dim]Fetching playlist information...[/dim]")
        playlist_info = self.downloader.get_playlist_info(playlist_url)
        
        if not playlist_info:
            console.print("[red]Failed to fetch playlist information[/red]")
            input("\nPress Enter to continue...")
            return
        
        playlist_title = playlist_info.get('title', 'Unknown Playlist')
        video_count = playlist_info.get('playlist_count', 0)
        
        console.print(f"\n[green]✓ Found playlist: {playlist_title}[/green]")
        console.print(f"[green]  Videos: {video_count}[/green]")
        
        # Format type
        console.print("\n[yellow]Step 2: Download Format[/yellow]")
        format_type = Prompt.ask(
            "Format type",
            choices=["video", "audio"],
            default="video"
        )
        
        # Quality
        console.print("\n[yellow]Step 3: Quality Settings[/yellow]")
        
        if format_type == "video":
            quality = Prompt.ask(
                "Video quality",
                choices=["best", "1080p", "720p", "480p", "360p"],
                default=self.config_manager.config.default_video_quality
            )
        else:
            quality = Prompt.ask(
                "Audio quality (kbps)",
                choices=["320", "256", "192", "128"],
                default=self.config_manager.config.default_audio_quality
            )
        
        # Output directory
        console.print("\n[yellow]Step 4: Output Settings[/yellow]")
        default_output = f"downloads/{playlist_title.replace(' ', '_')}"
        output_dir = Prompt.ask(
            "Output directory",
            default=default_output
        )
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Filename template
        filename_template = Prompt.ask(
            "Filename template",
            default=self.config_manager.config.default_filename_template
        )
        
        # Download order
        download_order = Prompt.ask(
            "Download order",
            choices=["newest_first", "oldest_first", "as_listed"],
            default="newest_first"
        )
        
        # Storage provider
        console.print("\n[yellow]Step 5: Storage Options[/yellow]")
        storage_provider = Prompt.ask(
            "Storage provider",
            choices=["local"] + list(self.config_manager.config.storage_providers.keys()),
            default="local"
        )
        
        # Create queue
        queue = Queue(
            id=None,
            playlist_url=playlist_url,
            playlist_title=playlist_title,
            format_type=format_type,
            quality=quality,
            output_dir=output_dir,
            filename_template=filename_template,
            download_order=download_order,
            storage_provider=storage_provider,
            storage_video_quality=None,
            storage_audio_quality=None,
            created_at=datetime.now().isoformat(),
            started_at=None,
            completed_at=None,
            status='pending'
        )
        
        # Save queue
        queue_id = self.queue_manager.create_queue(queue)
        queue.id = queue_id
        
        console.print(f"\n[green]✓ Queue created: {playlist_title}[/green]")
        
        # Add items to queue
        console.print("\n[dim]Adding videos to queue...[/dim]")
        
        entries = playlist_info.get('entries', [])
        added_count = 0
        
        for entry in entries:
            if not entry:
                continue
            
            item = DownloadItem(
                id=None,
                queue_id=queue_id,
                url=entry.get('url', ''),
                title=entry.get('title', 'Unknown'),
                video_id=entry.get('id'),
                uploader=entry.get('uploader'),
                upload_date=entry.get('upload_date'),
                file_path=None,
                file_size_bytes=None,
                file_hash=None,
                status='pending',
                error=None,
                download_started_at=None,
                download_completed_at=None,
                download_duration_seconds=None
            )
            
            self.queue_manager.add_item(item)
            added_count += 1
        
        console.print(f"[green]✓ Added {added_count} videos to queue[/green]")
        
        # Ask to download now
        if Confirm.ask("\nDownload queue now?", default=False):
            self.downloader.download_queue(queue, self.queue_manager)
        
        input("\nPress Enter to continue...")
