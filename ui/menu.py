"""Main menu"""
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

from managers.config_manager import ConfigManager
from managers.queue_manager import QueueManager
from managers.stats_manager import StatsManager
from managers.monitor_manager import MonitorManager
from downloaders.playlist import PlaylistDownloader
from utils.storage_providers import StorageManager

console = Console()


class Menu:
    """Main application menu"""
    
    def __init__(self):
        # Get all managers internally
        self.config_manager = ConfigManager()
        self.queue_manager = QueueManager()
        self.stats_manager = StatsManager()
        self.monitor_manager = MonitorManager()
        self.storage_manager = StorageManager()
        self.downloader = PlaylistDownloader()
    
    def show(self):
        """Display main menu"""
        while True:
            console.clear()
            
            # Get proxy count
            proxy_count = len(self.config_manager.config.proxies) if self.config_manager.config.proxies else 0
            proxy_text = f" | Proxies: {proxy_count}" if proxy_count > 0 else ""
            
            header = Panel(
                f"[bold cyan]YouTube Playlist Downloader[/bold cyan]{proxy_text}\n"
                "Advanced download management system",
                border_style="cyan"
            )
            console.print(header)
            
            # Show quick stats
            self._show_quick_stats()
            
            console.print("\n[cyan]Main Menu:[/cyan]")
            console.print("  1. Add new download queue")
            console.print("  2. View queues")
            console.print("  3. Download queue")
            console.print("  4. View statistics")
            console.print("  5. Channel monitoring")
            console.print("  6. Storage management")
            console.print("  7. Settings")
            console.print("  8. Exit")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                default="8"
            )
            
            if choice == "1":
                self._add_queue()
            elif choice == "2":
                self._view_queues()
            elif choice == "3":
                self._download_queue()
            elif choice == "4":
                self._resume_queue()
            elif choice == "5":
                self._view_statistics()
            elif choice == "6":
                from ui.monitoring_menu import MonitoringMenu
                monitoring_menu = MonitoringMenu()
                monitoring_menu.show()
            elif choice == "7":
                from ui.storage_menu import StorageMenu
                storage_menu = StorageMenu()
                storage_menu.show()
            elif choice == "8":
                from ui.settings_menu import SettingsMenu
                settings_menu = SettingsMenu()
                settings_menu.show()
            elif choice == "9":
                if Confirm.ask("\n[yellow]Exit application?[/yellow]", default=False):
                    console.print("\n[green]Goodbye![/green]")
                    break
    
    def _show_quick_stats(self):
        """Show quick statistics"""
        today_stats = self.stats_manager.get_today_stats()
        
        table = Table(show_header=False, box=None)
        table.add_column("Label", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row(
            "Today's Downloads:",
            f"{today_stats.total_downloads} ({today_stats.successful_downloads} successful)"
        )
        table.add_row(
            "Data Downloaded:",
            f"{today_stats.total_file_size_bytes / (1024**3):.2f} GB"
        )
        
        queues = self.queue_manager.get_all_queues()
        pending_queues = [q for q in queues if q.status == 'pending']
        
        table.add_row(
            "Pending Queues:",
            str(len(pending_queues))
        )
        
        console.print(table)
    
    def _add_queue(self):
        """Add new download queue"""
        from ui.queue_builder import QueueBuilder
        builder = QueueBuilder()
        builder.build_queue()
    
    def _view_queues(self):
        """View all queues"""
        from ui.queue_viewer import QueueViewer
        viewer = QueueViewer()
        viewer.show()
    
    def _download_queue(self):
        """Download a queue"""
        queues = self.queue_manager.get_all_queues()
        pending_queues = [q for q in queues if q.status == 'pending']
        
        if not pending_queues:
            console.print("[yellow]No pending queues found[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Pending Queues:[/cyan]")
        for idx, queue in enumerate(pending_queues, 1):
            console.print(f"  {idx}. {queue.playlist_title}")
        
        choice = IntPrompt.ask(
            "\nSelect queue",
            choices=[str(i) for i in range(1, len(pending_queues) + 1)]
        )
        
        selected_queue = pending_queues[choice - 1]
        
        # Ask if user wants to download all or just pending
        download_all = Confirm.ask(
            "\n[yellow]Download all items (ignoring past download logs)?[/yellow]",
            default=False
        )
        
        self.downloader.download_queue(selected_queue, self.queue_manager, download_all=download_all)
        
        input("\nPress Enter to continue...")
    
    def _resume_queue(self):
        """Resume an interrupted queue"""
        # Get resumable queues
        resumable = self.queue_manager.get_resumable_queues()
        
        if not resumable:
            console.print("[yellow]No resumable queues found[/yellow]")
            console.print("\n[dim]Tip: Interrupted downloads are automatically marked for resume[/dim]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Resumable Queues:[/cyan]")
        for idx, info in enumerate(resumable, 1):
            console.print(f"  {idx}. {info['playlist_title']} ({info['pending_count']} items pending)")
        
        choice = IntPrompt.ask(
            "\nSelect queue to resume",
            choices=[str(i) for i in range(1, len(resumable) + 1)]
        )
        
        selected_info = resumable[choice - 1]
        selected_queue = self.queue_manager.get_queue(selected_info['queue_id'])
        
        if not selected_queue:
            console.print("[red]Error: Queue not found[/red]")
            input("\nPress Enter to continue...")
            return
        
        console.print(f"\n[green]Resuming: {selected_queue.playlist_title}[/green]")
        console.print(f"[dim]{selected_info['pending_count']} items remaining[/dim]")
        
        self.downloader.download_queue(selected_queue, self.queue_manager, download_all=False)
        
        input("\nPress Enter to continue...")
    
    def _view_statistics(self):
        """View statistics"""
        from ui.stats_viewer import StatsViewer
        viewer = StatsViewer()
        viewer.show()
    
    def _download_settings(self):
        """Download settings submenu"""
        from ui.download_settings_menu import DownloadSettingsMenu
        menu = DownloadSettingsMenu()
        menu.show()
    
    def _network_settings(self):
        """Network & proxy settings submenu"""
        from ui.network_settings_menu import NetworkSettingsMenu
        menu = NetworkSettingsMenu()
        menu.show()
    
    def _notification_settings(self):
        """Notification settings submenu"""
        from ui.notification_settings_menu import NotificationSettingsMenu
        menu = NotificationSettingsMenu()
        menu.show()
    
    def _system_info(self):
        """Show system information"""
        from ui.setup_wizard import StatusPage
        status = StatusPage()
        status.show()
        input("\nPress Enter to continue...")
