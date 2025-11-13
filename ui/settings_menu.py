"""Settings menu"""
from rich.console import Console
from rich.prompt import Prompt

from managers.config_manager import ConfigManager

console = Console()


class SettingsMenu:
    """Settings configuration menu"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def show(self):
        """Show settings menu"""
        while True:
            console.clear()
            
            from rich.panel import Panel
            header = Panel(
                "[bold cyan]Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            options = [
                ("1", "Configure authentication"),
                ("2", "Manage proxies"),
                ("3", "Configure parallel downloads"),
                ("4", "Configure filename template"),
                ("5", "Configure Slack notifications"),
                ("6", "Configure email notifications"),
                ("7", "Toggle notification providers"),
                ("8", "Configure notification preferences"),
                ("9", "Configure download timeout"),
                ("10", "Configure alert thresholds"),
                ("11", "Configure rate limiting"),
                ("12", "Configure bandwidth limit"),
                ("13", "Configure live streams"),
                ("14", "Configure default quality"),
                ("15", "Configure filename normalization"),
                ("16", "Manage storage providers"),
                ("17", "View system status"),
                ("18", "Seed database"),
                ("19", "Migrate configuration"),
                ("20", "Reset configuration"),
                ("21", "Back to main menu")
            ]
            
            for num, desc in options:
                console.print(f"  {num}. {desc}")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=[opt[0] for opt in options],
                default="21"
            )
            
            if choice == "1":
                self.config_manager.configure_authentication()
            elif choice == "2":
                self.config_manager.manage_proxies()
            elif choice == "3":
                self.config_manager.configure_parallel_downloads()
            elif choice == "4":
                self.config_manager.configure_filename_template()
            elif choice == "5":
                self.config_manager.configure_slack_webhook()
            elif choice == "6":
                self.config_manager.configure_email_notifications()
            elif choice == "7":
                self.config_manager.toggle_notification_provider()
            elif choice == "8":
                self.config_manager.configure_notification_preferences()
            elif choice == "9":
                self.config_manager.configure_download_timeout()
            elif choice == "10":
                self.config_manager.configure_alert_thresholds()
            elif choice == "11":
                self.config_manager.configure_rate_limiting()
            elif choice == "12":
                self.config_manager.configure_bandwidth_limit()
            elif choice == "13":
                self.config_manager.configure_live_streams()
            elif choice == "14":
                self.config_manager.configure_default_quality()
            elif choice == "15":
                self.config_manager.configure_filename_normalization()
            elif choice == "16":
                from ui.storage_menu import StorageMenu
                storage_menu = StorageMenu()
                storage_menu.show()
            elif choice == "17":
                from ui.setup_wizard import StatusPage
                status = StatusPage()
                status.show()
                input("\nPress Enter to continue...")
            elif choice == "18":
                self._seed_database()
            elif choice == "19":
                self.config_manager.migrate_config()
                input("\nPress Enter to continue...")
            elif choice == "20":
                self.config_manager.reset_config()
                input("\nPress Enter to continue...")
            elif choice == "21":
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
