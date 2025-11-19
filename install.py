#!/usr/bin/env python3
"""Installation script for YouTube Playlist Downloader"""
import sys
import subprocess
import os
from pathlib import Path
import time

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              YouTube Playlist Downloader - Installation                  ║
║                                                                           ║
║              Advanced download management system                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Print installation banner"""
    print(BANNER)
    print()


def print_section(title):
    """Print a section header"""
    print(f"\n{'═' * 75}")
    print(f"  {title}")
    print(f"{'═' * 75}\n")


def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version.split()[0]}")


def install_dependencies():
    """Install required packages"""
    print_section("Installing Required Packages")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    requirements_dev_file = Path(__file__).parent / "requirements-dev.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    print("Installing core dependencies from requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✓ Core dependencies installed\n")
    except subprocess.CalledProcessError:
        print("❌ Failed to install core dependencies")
        sys.exit(1)
    
    if requirements_dev_file.exists():
        print("Installing development dependencies from requirements-dev.txt...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_dev_file)
            ])
            print("✓ Development dependencies installed\n")
        except subprocess.CalledProcessError:
            print("⚠ Warning: Failed to install development dependencies (non-critical)")
    
    time.sleep(1)


def show_settings_summary():
    """Show default settings one section at a time"""
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Confirm
    
    console = Console()
    
    print_section("Default Configuration")
    
    # Download Settings
    print("\n📥 DOWNLOAD SETTINGS\n")
    download_table = Table(show_header=True, header_style="bold cyan")
    download_table.add_column("Setting", style="dim")
    download_table.add_column("Value", style="green")
    
    download_table.add_row("Default Video Quality", "720p")
    download_table.add_row("Default Audio Quality", "192 kbps")
    download_table.add_row("Parallel Downloads", "3")
    download_table.add_row("Download Timeout", "300s")
    download_table.add_row("Filename Normalization", "✓ Enabled")
    
    console.print(download_table)
    input("\nPress Enter to continue...")
    
    # Notification Settings
    print("\n📧 NOTIFICATION SETTINGS\n")
    notif_table = Table(show_header=True, header_style="bold cyan")
    notif_table.add_column("Setting", style="dim")
    notif_table.add_column("Value", style="yellow")
    
    notif_table.add_row("Notifications Enabled", "✗ No")
    notif_table.add_row("Slack", "✗ Not configured")
    notif_table.add_row("Email", "✗ Not configured")
    notif_table.add_row("Daily Summary", "✗ Disabled")
    notif_table.add_row("Weekly Stats", "✗ Disabled")
    
    console.print(notif_table)
    input("\nPress Enter to continue...")
    
    # Rate Limiting
    print("\n⏱️  RATE LIMITING\n")
    rate_table = Table(show_header=True, header_style="bold cyan")
    rate_table.add_column("Setting", style="dim")
    rate_table.add_column("Value", style="green")
    
    rate_table.add_row("Max Downloads per Hour", "50")
    rate_table.add_row("Min Delay", "2.0s")
    rate_table.add_row("Max Delay", "5.0s")
    rate_table.add_row("Bandwidth Limit", "Unlimited")
    
    console.print(rate_table)
    input("\nPress Enter to continue...")
    
    # Storage Settings
    print("\n💾 STORAGE SETTINGS\n")
    storage_table = Table(show_header=True, header_style="bold cyan")
    storage_table.add_column("Setting", style="dim")
    storage_table.add_column("Value", style="green")
    
    storage_table.add_row("Default Storage", "LOCAL")
    storage_table.add_row("Storage Providers", "0")
    
    console.print(storage_table)
    
    print("\n" + "─" * 75)
    print("These are the default settings that will be used.")
    
    return Confirm.ask("\n🔧 Would you like to customize these settings now?", default=False)


def initialize_database():
    """Initialize database and test connection"""
    print_section("Database Initialization")
    
    from database import get_database_connection
    from managers.database_manager import DatabaseManager
    
    print("Creating database connection...")
    try:
        db = get_database_connection(db_type="sqlite", db_path="downloads.db")
        print("✓ Database connection established")
        
        print("\nInitializing database schema...")
        db_manager = DatabaseManager()
        
        # Test connection
        print("✓ Database schema initialized")
        print(f"✓ Database file: downloads.db")
        
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def seed_database():
    """Seed database with initial data"""
    print_section("Database Seeding")
    
    from rich.prompt import Confirm
    
    seed_db = Confirm.ask("Would you like to seed the database with sample data?", default=False)
    
    if seed_db:
        try:
            print("\nSeeding database...")
            import seed_database
            print("✓ Database seeded successfully")
        except Exception as e:
            print(f"⚠ Warning: Database seeding failed: {e}")
    else:
        print("⊘ Skipping database seeding")
    
    time.sleep(0.5)


def create_directories():
    """Create necessary directories"""
    print_section("Creating Directories")
    
    directories = [
        "downloads",
        "logs",
        "data"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {directory}/")
        else:
            print(f"⊙ Exists:  {directory}/")
    
    time.sleep(0.5)


def run_setup_wizard():
    """Run the setup wizard for custom configuration"""
    print_section("Configuration Wizard")
    
    from ui.setup_wizard import SetupWizard
    
    print("Starting configuration wizard...\n")
    wizard = SetupWizard()
    wizard.run()


def main():
    """Main installation process"""
    try:
        print_banner()
        
        # Check Python version
        print_section("System Requirements Check")
        check_python_version()
        
        # Check system dependencies
        check_system_dependencies()
        
        # Install dependencies
        install_dependencies()
        
        # Now we can import rich and other dependencies
        from rich.console import Console
        console = Console()
        
        # Create directories
        create_directories()
        
        # Show settings summary
        customize = show_settings_summary()
        
        # Initialize database
        if not initialize_database():
            print("\n❌ Installation failed due to database error")
            sys.exit(1)
        
        # Seed database
        seed_database()
        
        # Run setup wizard if requested
        if customize:
            run_setup_wizard()
        else:
            # Create default config
            print_section("Creating Default Configuration")
            from managers.config_manager import ConfigManager
            config_manager = ConfigManager()
            config_manager.config.setup_completed = True
            config_manager.save_config()
            print("✓ Default configuration saved")
        
        # Installation complete
        print_section("Installation Complete")
        console.print("\n[bold green]✓ Installation completed successfully![/bold green]\n")
        console.print("You can now run the application with:")
        console.print("  [cyan]./run.sh[/cyan]")
        console.print("  or")
        console.print("  [cyan]python main.py[/cyan]\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
