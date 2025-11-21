"""Notifications settings submenu"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from managers.config_manager import ConfigManager

console = Console()


class NotificationsSubmenu:
    """Notifications configuration submenu"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
    
    def show(self):
        """Show notifications settings menu"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Notification Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n1. Configure Slack notifications")
            console.print("2. Configure email notifications")
            console.print("3. Toggle notification providers")
            console.print("4. Configure notification preferences")
            console.print("5. Configure alert thresholds")
            console.print("0. Back")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "0"],
                default="0"
            )
            
            if choice == "1":
                self.config_manager.configure_slack_webhook()
            elif choice == "2":
                self.config_manager.configure_email_notifications()
            elif choice == "3":
                self.config_manager.toggle_notification_provider()
            elif choice == "4":
                self.config_manager.configure_notification_preferences()
            elif choice == "5":
                self.config_manager.configure_alert_thresholds()
            elif choice == "0":
                break
