"""Main application entry point"""
import sys
from pathlib import Path

# Rich imports
from rich.console import Console

# Manager imports
from managers.config_manager import ConfigManager
from managers.notification_manager import NotificationManager

# UI imports
from ui.menu import Menu
from ui.setup_wizard import SetupWizard

# Initialize console globally
console = Console()


def main():
    """Main application loop"""
    try:
        # Check if running in Colab
        if IN_COLAB:
            console.print("[yellow]⚠️  Running in Google Colab detected[/yellow]")
            console.print()
            console.print("Interactive menu is not available in Colab.")
            console.print("Please use the [cyan]colab_setup.py[/cyan] module instead.")
            console.print()
            console.print("Quick start:")
            console.print("  [dim]>>> from colab_setup import colab_help[/dim]")
            console.print("  [dim]>>> colab_help()[/dim]")
            console.print()
            console.print("Or for one-command download:")
            console.print("  [dim]>>> from colab_setup import colab_quick_download[/dim]")
            console.print("  [dim]>>> colab_quick_download('https://youtube.com/playlist?list=...')[/dim]")
            return
        
        console.clear()
        
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Run setup wizard if needed (no arguments!)
        if not config_manager.config.setup_completed:
            wizard = SetupWizard()
            wizard.run()
        
        # Initialize notification manager
        notification_manager = NotificationManager(config_manager.config)
        
        # Show notification status
        if notification_manager.has_any_notifier():
            console.print()
        
        # Main menu loop
        menu = Menu()
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
