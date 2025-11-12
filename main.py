"""Main application entry point"""
import sys
from pathlib import Path

# Rich imports
from rich.console import Console
from rich.prompt import Prompt

# Manager imports
from managers.config_manager import ConfigManager
from managers.queue_manager import QueueManager
from managers.stats_manager import StatsManager
from managers.proxy_manager import ProxyManager
from managers.monitor_manager import MonitorManager
from managers.notification_manager import NotificationManager

# Downloader imports
from downloaders.playlist import PlaylistDownloader

# UI imports
from ui.menu import Menu
from ui.settings_menu import SettingsMenu
from ui.monitoring_menu import MonitoringMenu
from ui.storage_menu import StorageMenu
from ui.setup_wizard import SetupWizard, StatusPage

# Utility imports
from utils.storage_providers import StorageManager

# Initialize console globally
console = Console()


def main():
    """Main application loop"""
    try:
        console.clear()
        
        # Initialize managers
        config_manager = ConfigManager()
        queue_manager = QueueManager()
        stats_manager = StatsManager()
        proxy_manager = ProxyManager()
        monitor_manager = MonitorManager()
        storage_manager = StorageManager()
        
        # Initialize notification manager (handles all notifiers)
        notification_manager = NotificationManager()
        
        # Show notification status
        notifier_status = notification_manager.get_status()
        if notifier_status['any_configured']:
            console.print()
        
        # Initialize downloader
        downloader = PlaylistDownloader()
        
        # Run setup wizard if needed
        if not config_manager.config.setup_completed:
            wizard = SetupWizard()
            if wizard.run():
                # Reload notification manager with new config
                notification_manager.reload_config(config_manager.config)
        
        # Main menu loop
        menu = Menu(
            config_manager,
            queue_manager,
            downloader,
            stats_manager,
            storage_manager,
            monitor_manager
        )
        menu.show()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Application terminated by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
