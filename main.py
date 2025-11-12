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
