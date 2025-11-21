"""Download settings submenu"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from managers.config_manager import ConfigManager

console = Console()


class DownloadSettingsSubmenu:
    """Download configuration submenu"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
    
    def show(self):
        """Show download settings menu"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Download Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n1. Configure default quality")
            console.print("2. Configure parallel downloads")
            console.print("3. Configure download timeout")
            console.print("4. Configure filename template")
            console.print("5. Configure filename normalization")
            console.print("0. Back")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "0"],
                default="0"
            )
            
            if choice == "1":
                self.config_manager.configure_default_quality()
            elif choice == "2":
                self.config_manager.configure_parallel_downloads()
            elif choice == "3":
                self.config_manager.configure_download_timeout()
            elif choice == "4":
                self.config_manager.configure_filename_template()
            elif choice == "5":
                self.config_manager.configure_filename_normalization()
            elif choice == "0":
                break
