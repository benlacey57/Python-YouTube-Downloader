"""Monitoring menu"""
from rich.console import Console

console = Console()


class MonitoringMenu:
    """Channel monitoring menu"""
    
    def __init__(self):
        from managers.monitor_manager import MonitorManager
        
        self.monitor_manager = MonitorManager()
    
    def show(self):
        """Display monitoring menu"""
        console.print("\n")

        status = "Running" if monitor_manager.is_running else "Stopped"
        channels = monitor_manager.get_all_channels()

        status_panel = Panel(
            f"[bold]Status:[/bold] {status}\n"
            f"[cyan]Monitored Channels:[/cyan] {len([c for c in channels if c.is_monitored])}",
            title="[bold]Monitoring Status[/bold]",
            border_style="cyan"
        )
        console.print(status_panel)

        # List monitored channels
        monitored = [c for c in channels if c.is_monitored]
        if monitored:
            channel_table = Table(title="Monitored Channels", show_header=True)
            channel_table.add_column("Title", style="cyan")
            channel_table.add_column("Format", style="yellow")
            channel_table.add_column("Interval", style="green")
            channel_table.add_column("Last Checked", style="white")
            channel_table.add_column("Status", style="magenta")

            for channel in monitored:
                last_checked = channel.last_checked or "Never"
                if channel.last_checked:
                    dt = datetime.fromisoformat(channel.last_checked)
                    last_checked = dt.strftime("%Y-%m-%d %H:%M")

                status_indicator = "Active" if channel.enabled else "Inactive"

                channel_table.add_row(
                    channel.title[:40],
                    channel.format_type,
                    f"{channel.check_interval_minutes}m",
                    last_checked,
                    status_indicator
                )

            console.print("\n")
            console.print(channel_table)

        options = [
            ("1", "Add channel to monitoring"),
            ("2", "Remove channel from monitoring"),
            ("3", "Start monitoring"),
            ("4", "Stop monitoring"),
            ("5", "Check now"),
            ("6", "Back to main menu")
        ]

        option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
        console.print(f"\n{option_text}\n")

        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=[num for num, _ in options],
            default="6"
        )

        return choice

    @staticmethod
    def add_channel_to_monitoring(monitor_manager, downloader, config_manager):
        """Add a channel to monitoring"""
        from models.channel import Channel
        from enums import DownloadFormat

        playlist_url = Prompt.ask("\n[cyan]Enter playlist URL[/cyan]")

        console.print("\n[yellow]Fetching playlist information...[/yellow]")
        console.print("[dim]This may take a moment...[/dim]")
        
        playlist_info = downloader.get_playlist_info(playlist_url)

        if not playlist_info:
            console.print("[red]Failed to fetch playlist information[/red]")
            console.print("\n[yellow]Troubleshooting tips:[/yellow]")
            console.print("  1. Check the URL is correct")
            console.print("  2. Try configuring authentication in Settings")
            console.print("  3. Check your internet connection")
            console.print("  4. Try using a different proxy (if enabled)")
            return

        playlist_title = playlist_info.get('title', 'Unknown Playlist')
        console.print(f"\n[green]Found playlist:[/green] {playlist_title}")

        # Try to extract channel URL
        channel_url = playlist_info.get('channel_url', playlist_url)
        uploader = playlist_info.get('uploader', 'Unknown')

        format_choice = Prompt.ask(
            "Download format",
            choices=["video", "audio"],
            default="video"
        )
        format_type = DownloadFormat.VIDEO.value if format_choice == "video" else DownloadFormat.AUDIO.value

        quality = MonitoringMenu._get_quality_choice(format_type)

        default_dir = f"downloads/{playlist_title}"
        output_dir = Prompt.ask("Output directory", default=default_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        interval = IntPrompt.ask("Check interval (minutes)", default=60)

        use_template = Confirm.ask(
            f"Use filename template? (default: {config_manager.config.default_filename_template})",
            default=True
        )
        filename_template = config_manager.config.default_filename_template if use_template else None

        download_order = MonitoringMenu._get_download_order()

        # Check if channel already exists
        existing_channel = monitor_manager.get_channel_by_url(channel_url)

        if existing_channel:
            # Update existing channel
            existing_channel.title = uploader or playlist_title
            existing_channel.is_monitored = True
            existing_channel.check_interval_minutes = interval
            existing_channel.format_type = format_type
            existing_channel.quality = quality
            existing_channel.output_dir = output_dir
            existing_channel.filename_template = filename_template
            existing_channel.download_order = download_order
            monitor_manager.update_channel(existing_channel)
            console.print(f"\n[green]Updated monitoring for {existing_channel.title}[/green]")
        else:
            # Create new channel
            channel = Channel(
                id=None,
                url=channel_url,
                title=uploader or playlist_title,
                is_monitored=True,
                check_interval_minutes=interval,
                format_type=format_type,
                quality=quality,
                output_dir=output_dir,
                filename_template=filename_template,
                download_order=download_order
            )
            monitor_manager.add_channel(channel)
            console.print(f"\n[green]Added {channel.title} to monitoring[/green]")

    @staticmethod
    def remove_channel_from_monitoring(monitor_manager):
        """Remove a channel from monitoring"""
        channels = monitor_manager.get_all_channels()
        monitored = [c for c in channels if c.is_monitored]

        if not monitored:
            console.print("\n[yellow]No monitored channels[/yellow]")
            return

        console.print("\n[cyan]Monitored Channels:[/cyan]")
        for idx, channel in enumerate(monitored, 1):
            console.print(f"  {idx}. {channel.title}")

        selection = IntPrompt.ask(
            "Select channel to remove (0 to cancel)",
            default=0
        )

        if selection > 0 and selection <= len(monitored):
            channel = monitored[selection - 1]
            channel.is_monitored = False
            monitor_manager.update_channel(channel)
            console.print(f"[green]Removed {channel.title} from monitoring[/green]")

    @staticmethod
    def _get_quality_choice(format_type: str) -> str:
        """Get quality selection from user"""
        if format_type == "audio":
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

    @staticmethod
    def _get_download_order() -> str:
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
