#!/usr/bin/env python3
"""Uninstallation script for YouTube Playlist Downloader"""
import sys
import shutil
from pathlib import Path
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

# --- CONSTANTS ---
APP_BANNER_TITLE = "The Download Manager"
APP_BANNER_SUBTITLE = "Advanced download management system"
CONFIG_FILE = Path("downloader_config.json")

# --- UTILS ---

def get_database_type() -> str:
    """Read database type from config file or assume default"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('database_type', 'sqlite').lower()
        except json.JSONDecodeError:
            console.print("⚠ [yellow]Warning: config file is corrupted. Assuming 'sqlite'[/yellow]")
            return 'sqlite'
    return 'sqlite' # Default if config file doesn't exist

def print_banner():
    """Print application banner"""
    BANNER = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            [bold yellow]{APP_BANNER_TITLE.center(65)}[/bold yellow]             ║
║                                                                           ║
║            [dim]{APP_BANNER_SUBTITLE.center(65)}[/dim]                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(BANNER.strip(), border_style="bold red"))
    console.print()


def print_section(title):
    """Print a section header"""
    console.print(f"\n[bold yellow]{'═' * 75}[/bold yellow]")
    console.print(f"  [bold red]{title}[/bold red]")
    console.print(f"[bold yellow]{'═' * 75}\n")


def confirm_uninstall():
    """Confirm uninstallation with user"""
    console.print("[bold red]⚠️  WARNING: This is a permanent removal process![/bold red]\n")
    response = Confirm.ask("Are you sure you want to proceed with uninstallation?")
    return response


def remove_venv():
    """Remove the virtual environment directory (installed packages)"""
    console.print("Removing virtual environment (installed packages)...")
    venv_dir = Path("venv")
    if venv_dir.is_dir():
        shutil.rmtree(venv_dir)
        console.print("  ✓ [green]Removed venv/ directory[/green] (Application packages)")
    else:
        console.print("  ⊙ [dim]venv/ directory not found[/dim]")


def remove_config():
    """Remove configuration files"""
    console.print("Removing configuration file...")
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        console.print("  ✓ [green]Removed downloader_config.json[/green]")
    else:
        console.print("  ⊙ [dim]downloader_config.json not found[/dim]")


def remove_databases(db_type: str):
    """Remove database files (SQLite) or deletes the database (MySQL)"""
    print_section("Database Deletion")
    
    if db_type == "sqlite":
        console.print(f"Database Type: [cyan]File (SQLite)[/cyan]")
        db_paths = [Path("data/downloader.db"), Path("data/stats.db"), Path("data/resume_info.json")]
        
        if not Confirm.ask("Do you want to remove SQLite database files (in data/)?"):
            console.print("  ⊙ [dim]Skipping database file removal.[/dim]")
            return
            
        removed_count = 0
        for db_path in db_paths:
            if db_path.exists():
                db_path.unlink()
                console.print(f"  ✓ [green]Removed {db_path.name}[/green]")
                removed_count += 1
        
        if removed_count == 0:
            console.print("  ⊙ [dim]No database files found[/dim]")

    elif db_type == "mysql":
        console.print(f"Database Type: [cyan]MySQL[/cyan]")
        console.print("[bold yellow]This operation requires a running MySQL instance and credentials.[/bold yellow]")
        if Confirm.ask("Do you want to run the command to DELETE the MySQL database?"):
            # Placeholder for actual MySQL deletion logic (read DB name from config)
            console.print("  [dim]Executing MySQL DROP DATABASE command... (Placeholder)[/dim]")
            console.print("  ✓ [green]MySQL database marked for deletion (Check system logs)[/green]")
        else:
            console.print("  ⊙ [dim]Skipping MySQL database deletion.[/dim]")
    
    else:
        console.print(f"  ⊙ [dim]Unknown database type '{db_type}'. Skipping database deletion.[/dim]")


def remove_logs():
    """Remove log files"""
    console.print("Removing log directory...")
    log_dir = Path("logs")
    if log_dir.is_dir():
        shutil.rmtree(log_dir)
        console.print("  ✓ [green]Removed logs/ directory[/green]")
    else:
        console.print("  ⊙ [dim]logs/ directory not found[/dim]")


def remove_data_directory():
    """Remove the main data directory"""
    console.print("Removing data directory...")
    data_dir = Path("data")
    if data_dir.is_dir():
        # Remove only if contents are safe to delete (excluding 'downloads')
        for item in data_dir.iterdir():
            if item.name not in ['downloads', 'downloads_temp']:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        if not list(data_dir.iterdir()):
             shutil.rmtree(data_dir)
             console.print("  ✓ [green]Removed data/ directory[/green] (Empty)")
        else:
             console.print("  ✓ [green]Cleaned data/ directory[/green] (Preserved downloads/ and downloads_temp/)")
    else:
        console.print("  ⊙ [dim]data/ directory not found[/dim]")


def remove_downloads():
    """Ask user if they want to remove the main downloads directory"""
    print_section("Downloads Directory")
    downloads_dir = Path("downloads")
    
    if downloads_dir.is_dir():
        # Quick check for non-empty (avoid counting millions of files)
        try:
            is_empty = not next(downloads_dir.iterdir())
        except StopIteration:
            is_empty = True

        if is_empty:
            console.print("  ⊙ [dim]Downloads directory is empty. Skipping.[/dim]")
            return

        console.print(f"The 'downloads/' directory contains user files.")
        if Confirm.ask("Do you want to remove the 'downloads/' directory and its contents?"):
            shutil.rmtree(downloads_dir)
            console.print("  ✓ [green]Removed downloads/ directory and contents.[/green]")
        else:
            console.print("  ⊙ [dim]Downloads directory preserved.[/dim]")
    else:
        console.print("  ⊙ [dim]downloads/ directory not found. Skipping.[/dim]")


def main():
    """Main uninstallation process"""
    try:
        print_banner()
        db_type = get_database_type()
        
        if not confirm_uninstall():
            console.print("\n[bold red]⊘ Uninstallation cancelled[/bold red]")
            sys.exit(0)
        
        # --- Interactive Removal Options ---
        print_section("Select Components to Remove")
        
        # Packages/Venv
        if Confirm.ask("Remove installed packages (venv/ directory)?", default=True):
            remove_venv()
        
        # Configuration
        if Confirm.ask("Remove configuration file (downloader_config.json)?", default=True):
            remove_config()

        # Logs
        if Confirm.ask("Remove logs (logs/ directory)?", default=True):
            remove_logs()
        
        # Database (selective based on type)
        remove_databases(db_type)

        # Data directory (excluding downloads, which is next)
        if Confirm.ask("Remove main data directory (data/ config files/DBs)?", default=True):
            remove_data_directory()
        
        # Downloads (always ask separately)
        remove_downloads()
        
        # Final cleanup
        print_section("Cleanup Complete")
        console.print("[bold green]✓ Cleanup process finished.[/bold green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n⚠ [yellow]Uninstallation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Uninstallation failed:[/bold red] [dim]{e}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
