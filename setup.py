#!/usr/bin/env python3
"""
Configuration setup script: Handles interactive prompts for database, 
notifications, and sample data seeding. Saves final config.json.
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure venv is used for imports
sys.path.insert(0, str(Path("./venv/lib/python3.8/site-packages/")))

# Import Rich libraries
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt

# Import manager placeholders (assuming these exist in the project structure)
try:
    from managers.config_manager import ConfigManager
    from managers.queue_manager import QueueManager
except ImportError:
    # Fallback/mocking for environments where managers haven't been created yet
    class MockConfig:
        def __init__(self):
            self.setup_completed = False
            self.db_path = "data/downloads.db"
    class MockConfigManager:
        def __init__(self):
            self.config = MockConfig()
        def save_config(self):
            print("MOCK: Saving configuration...")

    class MockQueueManager:
        def __init__(self, **kwargs): pass
        def _init_database(self):
            print("MOCK: Database initialized.")
        def seed_data(self):
            print("MOCK: Sample data generated.")
        
    ConfigManager = MockConfigManager
    QueueManager = MockQueueManager

console = Console()

# --- CONSTANTS ---
APP_BANNER_TITLE = "The Download Manager"
APP_BANNER_SUBTITLE = "Configuration Wizard"
KNOWN_NOTIFIERS = ["Email", "Slack", "NewNotifier"] # Dynamic list of existing notifiers


# --- UTILS ---

def print_banner():
    """Print application banner"""
    BANNER = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              [bold yellow]{APP_BANNER_TITLE.center(65)}[/bold yellow]             ║
║                                                                           ║
║              [dim]{APP_BANNER_SUBTITLE.center(65)}[/dim]                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(BANNER.strip(), border_style="bold magenta"))
    console.print()


def print_section(title):
    """Print a section header"""
    console.print(f"\n[bold yellow]{'═' * 75}[/bold yellow]")
    console.print(f"  [bold cyan]{title}[/bold cyan]")
    console.print(f"[bold yellow]{'═' * 75}\n")


# --- CONFIGURATION PROMPTS ---

def _prompt_database_config() -> Dict:
    """Prompts user for database configuration details."""
    print_section("1. Database Configuration")
    
    db_choice = Prompt.ask(
        "Select database type", 
        choices=["file", "mysql"], 
        default="file"
    )
    
    config: Dict[str, Any] = {"DATABASE_TYPE": db_choice}
    
    if db_choice == "file":
        config["DB_PATH"] = Prompt.ask(
            "Enter path for SQLite file", 
            default="data/downloads.db"
        )
        console.print("  [dim]Using SQLite for file storage.[/dim]")
    
    elif db_choice == "mysql":
        console.print("\n[bold yellow]--- MySQL Details ---[/bold yellow]")
        config["MYSQL_HOST"] = Prompt.ask("MySQL Host", default="localhost")
        config["MYSQL_PORT"] = IntPrompt.ask("MySQL Port", default=3306)
        config["MYSQL_USER"] = Prompt.ask("MySQL User", default="root")
        config["MYSQL_PASSWORD"] = Prompt.ask("MySQL Password (hidden)", password=True, default="")
        config["MYSQL_DB"] = Prompt.ask("MySQL Database Name", default="downloader_db")
        
    return config


def _prompt_notification_config() -> Dict:
    """Prompts user to set up notification services."""
    print_section("2. Notification Configuration")
    
    if not Confirm.ask("Do you want to set up notification settings now?"):
        return {"NOTIFICATIONS_ENABLED": False}

    console.print("\n[bold yellow]Available Notifiers:[/bold yellow]")
    for i, notifier in enumerate(KNOWN_NOTIFIERS):
        console.print(f"  [cyan]{i+1}[/cyan]: {notifier}")
        
    notifier_index = IntPrompt.ask(
        "Select a notifier to configure (enter number)",
        choices=[str(i+1) for i in range(len(KNOWN_NOTIFIERS))],
        default=1
    )
    selected_notifier = KNOWN_NOTIFIERS[notifier_index - 1]
    
    console.print(f"Configuring [bold magenta]{selected_notifier}[/bold magenta]...")
    
    config: Dict[str, Any] = {
        "NOTIFICATIONS_ENABLED": True,
        "NOTIFIER_TYPE": selected_notifier
    }
    
    if selected_notifier == "Email":
        config["EMAIL_HOST"] = Prompt.ask("SMTP Host", default="smtp.example.com")
        config["EMAIL_USER"] = Prompt.ask("Email Username")
        config["EMAIL_PASSWORD"] = Prompt.ask("Email Password (hidden)", password=True)
    elif selected_notifier == "Slack":
        config["SLACK_WEBHOOK"] = Prompt.ask("Slack Webhook URL")
    else:
        config[f"{selected_notifier.upper()}_API_KEY"] = Prompt.ask(f"{selected_notifier} API Key")

    return config


def initialize_database(db_config: Dict):
    """Initializes the database tables."""
    print_section("3. Database Initialization")
    try:
        # Instantiate QueueManager with the config path/details
        if db_config["DATABASE_TYPE"] == "file":
            qm = QueueManager(db_path=db_config["DB_PATH"])
        else:
            # Assuming QueueManager handles MySQL connection logic
            qm = QueueManager(**db_config) 
            
        qm._init_database() 
        console.print("✓ [green]Database tables initialized successfully.[/green]")
        return True
    except Exception as e:
        console.print(f"❌ [bold red]Database initialization failed:[/bold red] [dim]{e}[/dim]")
        return False

def seed_database():
    """Seed the database with initial data (e.g., test queues)"""
    print_section("4. Sample Data")
    
    if Confirm.ask("Do you want to generate sample data?"):
        try:
            qm = QueueManager() # Re-initialize to ensure it picks up the current DB config
            qm.seed_data()
            console.print("✓ [green]Sample data generated and seeded successfully.[/green]")
        except Exception as e:
            console.print(f"❌ [bold red]Failed to seed data:[/bold red] [dim]{e}[/dim]")
    else:
        console.print("⊙ [dim]Skipping sample data generation.[/dim]")


def save_final_config(db_config: Dict, notif_config: Dict):
    """Saves the final configuration object."""
    print_section("5. Saving Configuration")
    
    # Other sensible defaults not asked for in prompts
    default_app_config = {
        "SETUP_COMPLETED": True,
        "DOWNLOAD_DIR": "downloads", 
        "MAX_CONCURRENT_DOWNLOADS": 3,
        # ... other settings
    }
    
    final_config_data = {
        **db_config,
        **notif_config,
        **default_app_config
    }
    
    try:
        config_manager = ConfigManager()
        # In a real ConfigManager, this would update or create the config.json
        config_manager.config.__dict__.update(final_config_data)
        config_manager.save_config()
        
        console.print("✓ [green]Configuration saved as config.json.[/green]")
    except Exception as e:
        console.print(f"❌ [bold red]Configuration save failed:[/bold red] [dim]{e}[/dim]")
        sys.exit(1)


def main():
    """Main configuration setup loop"""
    try:
        print_banner()
        
        # Check if config already exists and is complete
        config_manager = ConfigManager()
        if config_manager.config.setup_completed:
            if not Confirm.ask("[yellow]Configuration already complete.[/yellow] Do you want to re-run the wizard?"):
                console.print("\n[bold green]Configuration preserved. Exiting.[/bold green]")
                sys.exit(0)
        
        # 1. Prompt for Database config
        db_config = _prompt_database_config()

        # 2. Prompt for Notification config
        notif_config = _prompt_notification_config()
        
        # 3. Initialize database
        if not initialize_database(db_config):
            console.print("\n❌ [bold red]Configuration failed due to database error[/bold red]")
            sys.exit(1)
        
        # 4. Seed database
        seed_database()
        
        # 5. Save final configuration
        save_final_config(db_config, notif_config)
        
        # Configuration complete
        print_section("Setup Complete")
        console.print("\n[bold green]✓ Application is ready to run![/bold green]\n")
        console.print("To start the application, run:")
        console.print("  [cyan]./run.sh[/cyan] or [cyan]python main.py[/cyan]")
        
    except KeyboardInterrupt:
        console.print("\n\n⚠ [yellow]Configuration cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Configuration failed:[/bold red] [dim]{e}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
