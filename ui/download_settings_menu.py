"""Download settings submenu"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from managers.config_manager import ConfigManager

console = Console()


class DownloadSettingsMenu:
    """Download configuration submenu"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def show(self):
        """Show download settings menu"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Download Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n1. Default video quality")
            console.print("2. Default audio quality")
            console.print("3. Parallel downloads")
            console.print("4. Download timeout")
            console.print("5. Filename template")
            console.print("6. Filename normalization")
            console.print("7. Live stream settings")
            console.print("8. Authentication (cookies)")
            console.print("0. Back")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"],
                default="0"
            )
            
            if choice == "1":
                self.config_manager.configure_default_quality()
            elif choice == "2":
                self.config_manager.configure_default_quality()
            elif choice == "3":
                self.config_manager.configure_parallel_downloads()
            elif choice == "4":
                self.config_manager.configure_download_timeout()
            elif choice == "5":
                self.config_manager.configure_filename_template()
            elif choice == "6":
                self.config_manager.configure_filename_normalization()
            elif choice == "7":
                self.config_manager.configure_live_streams()
            elif choice == "8":
                self.config_manager.configure_authentication()
            elif choice == "0":
                break
