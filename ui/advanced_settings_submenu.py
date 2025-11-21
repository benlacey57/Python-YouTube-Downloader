"""Advanced settings submenu"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from managers.config_manager import ConfigManager

console = Console()


class AdvancedSettingsSubmenu:
    """Advanced configuration submenu"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
    
    def show(self):
        """Show advanced settings menu"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Advanced Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n1. Configure live streams")
            console.print("2. View system status")
            console.print("3. Seed database")
            console.print("4. Migrate configuration")
            console.print("5. Reset configuration")
            console.print("0. Back")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "0"],
                default="0"
            )
            
            if choice == "1":
                self.config_manager.configure_live_streams()
            elif choice == "2":
                from ui.setup_wizard import StatusPage
                status = StatusPage()
                status.show()
                input("\nPress Enter to continue...")
            elif choice == "3":
                self._seed_database()
            elif choice == "4":
                self.config_manager.migrate_config()
                input("\nPress Enter to continue...")
            elif choice == "5":
                self.config_manager.reset_config()
                input("\nPress Enter to continue...")
            elif choice == "0":
                break
    
    def _seed_database(self):
        """Seed database"""
        from utils.database_seeder import DatabaseSeeder
        from models.channel import Channel
        from managers.monitor_manager import MonitorManager
        from pathlib import Path
        
        seeder = DatabaseSeeder()
        monitor_manager = MonitorManager()
        
        # Callback for seeding channels
        def seed_channels_callback(record: dict):
            existing = monitor_manager.get_channel_by_url(record['url'])
            if existing:
                return "skipped"
            
            channel = Channel(
                id=None,
                url=record['url'],
                title=record['title'],
                is_monitored=record.get('is_monitored', False),
                check_interval_minutes=record.get('check_interval_minutes', 60),
                format_type=record.get('format_type', 'video'),
                quality=record.get('quality', '720p'),
                output_dir=record.get('output_dir', f"downloads/{record['title']}"),
                filename_template=record.get('filename_template', '{index:03d} - {title}'),
                download_order=record.get('download_order', 'newest_first'),
                enabled=record.get('enabled', True)
            )
            
            Path(channel.output_dir).mkdir(parents=True, exist_ok=True)
            monitor_manager.add_channel(channel)
            return "success"
        
        seeder.seed_from_json('channels', {'channels': seed_channels_callback})
        input("\nPress Enter to continue...")
