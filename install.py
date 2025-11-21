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


def check_system_dependencies():
    """Check for required system dependencies"""
    print("\nChecking system dependencies...")
    
    # Check for ffmpeg (recommended for yt-dlp)
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ ffmpeg installed: {version_line.split()[2] if len(version_line.split()) > 2 else 'version found'}")
        else:
            print("⚠ Warning: ffmpeg not found (recommended for best quality)")
    except FileNotFoundError:
        print("⚠ Warning: ffmpeg not found (recommended for best quality)")
        print("  Install with: sudo apt-get install ffmpeg (Ubuntu/Debian)")
        print("              or: brew install ffmpeg (macOS)")
    
    # Check for git (optional, for version control)
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ git installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print("⊙ git not found (optional)")
    
    time.sleep(0.5)


def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_dir = Path("venv")
    
    if venv_dir.exists():
        print("✓ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✓ Virtual environment created\n")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False


def install_dependencies():
    """Install required packages"""
    print_section("Installing Required Packages")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    requirements_dev_file = Path(__file__).parent / "requirements-dev.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Determine pip executable (use venv if it exists)
    venv_pip = Path("venv/bin/pip")
    pip_executable = str(venv_pip) if venv_pip.exists() else "pip3"
    
    print("Installing core dependencies from requirements.txt...")
    try:
        subprocess.check_call([
            pip_executable, "install", "-r", str(requirements_file)
        ])
        print("✓ Core dependencies installed\n")
    except subprocess.CalledProcessError:
        print("❌ Failed to install core dependencies")
        sys.exit(1)
    
    if requirements_dev_file.exists():
        print("Installing development dependencies from requirements-dev.txt...")
        try:
            subprocess.check_call([
                pip_executable, "install", "-r", str(requirements_dev_file)
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
    from database.migrations import run_migrations
    from managers.database_manager import DatabaseManager
    
    print("Creating database connection...")
    try:
        db = get_database_connection(db_type="sqlite", db_path="downloads.db")
        print("✓ Database connection established")
        
        print("\nInitializing database schema...")
        # Create base tables if they don't exist
        db_manager = DatabaseManager()
        print("✓ Base schema initialized")
        
        # Run migrations to update schema to latest version
        print("\nRunning database migrations...")
        if run_migrations("downloads.db"):
            print("✓ Database migrations completed")
        else:
            print("⚠️  Some migrations may have failed")
        
        print(f"\n✓ Database file: downloads.db")
        
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nℹ️  Tip: Try running with --fresh flag to remove all old data:")
        print("   python3 install.py --fresh")
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
        # Check for --fresh flag
        fresh_install = "--fresh" in sys.argv
        
        print_banner()
        
        if fresh_install:
            print("🔄 Fresh install mode: Will remove existing data directories\n")
            from rich.prompt import Confirm
            if Confirm.ask("⚠️  This will delete existing data, logs, and databases. Continue?", default=False):
                print("\nRemoving existing data...")
                import shutil
                
                # Remove data directories
                for dir_path in ["data", "logs", "downloads.db", "stats.db", "config.json", "downloader_config.json"]:
                    path = Path(dir_path)
                    if path.exists():
                        if path.is_dir():
                            shutil.rmtree(path)
                            print(f"  ✓ Removed {dir_path}/")
                        else:
                            path.unlink()
                            print(f"  ✓ Removed {dir_path}")
                    else:
                        print(f"  ⊛ {dir_path} not found")
                print("")
            else:
                print("\n⊛ Fresh install cancelled")
                sys.exit(0)
        
        # Check Python version
        print_section("System Requirements Check")
        check_python_version()
        
        # Check system dependencies
        check_system_dependencies()
        
        # Create virtual environment
        print_section("Virtual Environment Setup")
        if not create_virtual_environment():
            print("\n❌ Installation failed due to venv creation error")
            sys.exit(1)
        
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
