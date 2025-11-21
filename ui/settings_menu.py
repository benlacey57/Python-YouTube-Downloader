"""Settings menu"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

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
            
            header = Panel(
                "[bold cyan]Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n1. Download Settings")
            console.print("2. Network & Proxy Settings")
            console.print("3. Notifications")
            console.print("4. Storage Management")
            console.print("5. Advanced Settings")
            console.print("0. Back to main menu")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "0"],
                default="0"
            )
            
            if choice == "1":
                from ui.download_settings_submenu import DownloadSettingsSubmenu
                submenu = DownloadSettingsSubmenu(self.config_manager)
                submenu.show()
            elif choice == "2":
                from ui.network_settings_menu import NetworkSettingsMenu
                submenu = NetworkSettingsMenu(self.config_manager)
                submenu.show()
            elif choice == "3":
                from ui.notifications_submenu import NotificationsSubmenu
                submenu = NotificationsSubmenu(self.config_manager)
                submenu.show()
            elif choice == "4":
                from ui.storage_menu import StorageMenu
                submenu = StorageMenu()
                submenu.show()
            elif choice == "5":
                from ui.advanced_settings_submenu import AdvancedSettingsSubmenu
                submenu = AdvancedSettingsSubmenu(self.config_manager)
                submenu.show()
            elif choice == "0":
                break
