"""Monitoring menu"""
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

from managers.monitor_manager import MonitorManager
from models.channel import Channel
from pathlib import Path

console = Console()


class MonitoringMenu:
    """Channel monitoring menu"""
    
    def __init__(self):
        self.monitor_manager = MonitorManager()
    
    def show(self):
        """Show monitoring menu"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Channel Monitoring[/bold cyan]\n"
                "Monitor YouTube channels for new videos",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n[cyan]Options:[/cyan]")
            console.print("  1. View monitored channels")
            console.print("  2. Add channel")
            console.print("  3. Edit channel")
            console.print("  4. Delete channel")
            console.print("  5. Enable/Disable channel")
            console.print("  6. Check channel now")
            console.print("  7. Check all channels")
            console.print("  8. Back to main menu")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                default="8"
            )
            
            if choice == "1":
                self._view_channels()
            elif choice == "2":
                self._add_channel()
            elif choice == "3":
                self._edit_channel()
            elif choice == "4":
                self._delete_channel()
            elif choice == "5":
                self._toggle_channel()
            elif choice == "6":
                self._check_channel()
            elif choice == "7":
                self._check_all_channels()
            elif choice == "8":
                break
    
    def _view_channels(self):
        """View all monitored channels"""
        channels = self.monitor_manager.get_all_channels()
        
        if not channels:
            console.print("\n[yellow]No channels configured[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        table = Table(title="Monitored Channels", show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="green")
        table.add_column("Monitored", justify="center")
        table.add_column("Enabled", justify="center")
        table.add_column("Format", justify="center")
        table.add_column("Quality", justify="center")
        
        for idx, channel in enumerate(channels, 1):
            monitored = "✓" if channel.is_monitored else "✗"
            enabled = "✓" if channel.enabled else "✗"
            
            table.add_row(
                str(idx),
                channel.title,
                monitored,
                enabled,
                channel.format_type,
                channel.quality
            )
        
        console.print("\n")
        console.print(table)
        
        input("\nPress Enter to continue...")
    
    def _add_channel(self):
        """Add new channel to monitor"""
        console.clear()
        console.print(Panel("[bold cyan]Add Channel[/bold cyan]", border_style="cyan"))
        
        url = Prompt.ask("\nChannel URL")
        title = Prompt.ask("Channel title")
        
        is_monitored = Confirm.ask("Monitor this channel?", default=True)
        
        if is_monitored:
            check_interval = IntPrompt.ask(
                "Check interval (minutes)",
                default=1440
            )
        else:
            check_interval = 1440
        
        format_type = Prompt.ask(
            "Format type",
            choices=["video", "audio"],
            default="video"
        )
        
        if format_type == "video":
            quality = Prompt.ask(
                "Quality",
                choices=["best", "1080p", "720p", "480p", "360p"],
                default="720p"
            )
        else:
            quality = Prompt.ask(
                "Quality (kbps)",
                choices=["320", "256", "192", "128"],
                default="192"
            )
        
        output_dir = Prompt.ask(
            "Output directory",
            default=f"downloads/{title.replace(' ', '_')}"
        )
        
        filename_template = Prompt.ask(
            "Filename template",
            default="{index:03d} - {title}"
        )
        
        download_order = Prompt.ask(
            "Download order",
            choices=["newest_first", "oldest_first"],
            default="newest_first"
        )
        
        channel = Channel(
            id=None,
            url=url,
            title=title,
            is_monitored=is_monitored,
            check_interval_minutes=check_interval,
            format_type=format_type,
            quality=quality,
            output_dir=output_dir,
            filename_template=filename_template,
            download_order=download_order,
            enabled=True
        )
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.monitor_manager.add_channel(channel)
        
        console.print("\n[green]✓ Channel added[/green]")
        input("\nPress Enter to continue...")
    
    def _edit_channel(self):
        """Edit existing channel"""
        channels = self.monitor_manager.get_all_channels()
        
        if not channels:
            console.print("\n[yellow]No channels configured[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Channels:[/cyan]")
        for idx, channel in enumerate(channels, 1):
            console.print(f"  {idx}. {channel.title}")
        
        choice = IntPrompt.ask(
            "\nSelect channel",
            choices=[str(i) for i in range(1, len(channels) + 1)]
        )
        
        channel = channels[choice - 1]
        
        # Edit fields (similar to add_channel but with defaults)
        console.print(f"\n[cyan]Editing: {channel.title}[/cyan]")
        console.print("[dim]Press Enter to keep current value[/dim]\n")
        
        new_title = Prompt.ask("Channel title", default=channel.title)
        channel.title = new_title
        
        self.monitor_manager.update_channel(channel)
        
        console.print("\n[green]✓ Channel updated[/green]")
        input("\nPress Enter to continue...")
    
    def _delete_channel(self):
        """Delete channel"""
        channels = self.monitor_manager.get_all_channels()
        
        if not channels:
            console.print("\n[yellow]No channels configured[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Channels:[/cyan]")
        for idx, channel in enumerate(channels, 1):
            console.print(f"  {idx}. {channel.title}")
        
        choice = IntPrompt.ask(
            "\nSelect channel to delete",
            choices=[str(i) for i in range(1, len(channels) + 1)]
        )
        
        channel = channels[choice - 1]
        
        if Confirm.ask(f"\n[red]Delete '{channel.title}'?[/red]", default=False):
            self.monitor_manager.delete_channel(channel.id)
            console.print("\n[green]✓ Channel deleted[/green]")
        
        input("\nPress Enter to continue...")
    
    def _toggle_channel(self):
        """Enable/disable channel"""
        channels = self.monitor_manager.get_all_channels()
        
        if not channels:
            console.print("\n[yellow]No channels configured[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Channels:[/cyan]")
        for idx, channel in enumerate(channels, 1):
            status = "Enabled" if channel.enabled else "Disabled"
            console.print(f"  {idx}. {channel.title} [{status}]")
        
        choice = IntPrompt.ask(
            "\nSelect channel",
            choices=[str(i) for i in range(1, len(channels) + 1)]
        )
        
        channel = channels[choice - 1]
        channel.enabled = not channel.enabled
        
        self.monitor_manager.update_channel(channel)
        
        status = "enabled" if channel.enabled else "disabled"
        console.print(f"\n[green]✓ Channel {status}[/green]")
        input("\nPress Enter to continue...")
    
    def _check_channel(self):
        """Check single channel now"""
        channels = self.monitor_manager.get_all_channels()
        monitored = [c for c in channels if c.is_monitored and c.enabled]
        
        if not monitored:
            console.print("\n[yellow]No monitored channels[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Monitored Channels:[/cyan]")
        for idx, channel in enumerate(monitored, 1):
            console.print(f"  {idx}. {channel.title}")
        
        choice = IntPrompt.ask(
            "\nSelect channel",
            choices=[str(i) for i in range(1, len(monitored) + 1)]
        )
        
        channel = monitored[choice - 1]
        
        console.print(f"\n[cyan]Checking {channel.title}...[/cyan]")
        new_videos = self.monitor_manager.check_channel(channel.id)
        
        if new_videos:
            console.print(f"[green]✓ Found {len(new_videos)} new videos[/green]")
        else:
            console.print("[yellow]No new videos found[/yellow]")
        
        input("\nPress Enter to continue...")
    
    def _check_all_channels(self):
        """Check all monitored channels"""
        console.print("\n[cyan]Checking all monitored channels...[/cyan]\n")
        
        channels = self.monitor_manager.get_all_channels()
        monitored = [c for c in channels if c.is_monitored and c.enabled]
        
        if not monitored:
            console.print("[yellow]No monitored channels[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        total_new = 0
        
        for channel in monitored:
            console.print(f"Checking: {channel.title}")
            new_videos = self.monitor_manager.check_channel(channel.id)
            
            if new_videos:
                console.print(f"  [green]✓ Found {len(new_videos)} new videos[/green]")
                total_new += len(new_videos)
            else:
                console.print(f"  [dim]No new videos[/dim]")
        
        console.print(f"\n[green]✓ Check complete. Found {total_new} new videos total[/green]")
        input("\nPress Enter to continue...")
