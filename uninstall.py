#!/usr/bin/env python3
"""Uninstallation script for YouTube Playlist Downloader"""
import sys
import shutil
from pathlib import Path

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            YouTube Playlist Downloader - Uninstallation                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Print uninstallation banner"""
    print(BANNER)
    print()


def print_section(title):
    """Print a section header"""
    print(f"\n{'═' * 75}")
    print(f"  {title}")
    print(f"{'═' * 75}\n")


def confirm_uninstall():
    """Confirm uninstallation with user"""
    print("⚠️  WARNING: This will remove all application data!\n")
    print("The following will be deleted:")
    print("  • Configuration files")
    print("  • Database files (downloads.db, stats.db)")
    print("  • Log files")
    print("  • Virtual environment (if --fresh flag is used)")
    print()
    
    response = input("Are you sure you want to continue? [y/N]: ").strip().lower()
    return response in ['y', 'yes']


def remove_config():
    """Remove configuration files"""
    print("Removing configuration files...")
    
    config_file = Path("config.json")
    if config_file.exists():
        config_file.unlink()
        print("  ✓ Removed config.json")
    else:
        print("  ⊙ config.json not found")


def remove_databases():
    """Remove database files"""
    print("\nRemoving database files...")
    
    db_files = ["downloads.db", "stats.db"]
    for db_file in db_files:
        path = Path(db_file)
        if path.exists():
            path.unlink()
            print(f"  ✓ Removed {db_file}")
        else:
            print(f"  ⊙ {db_file} not found")


def remove_logs():
    """Remove log directory"""
    print("\nRemoving log files...")
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
        print("  ✓ Removed logs/ directory")
    else:
        print("  ⊙ logs/ directory not found")


def remove_data_directory():
    """Remove data directory"""
    print("\nRemoving data directory...")
    
    data_dir = Path("data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
        print("  ✓ Removed data/ directory")
    else:
        print("  ⊙ data/ directory not found")


def remove_downloads():
    """Ask about removing downloads directory"""
    print("\nDownloads directory...")
    
    downloads_dir = Path("downloads")
    if downloads_dir.exists():
        response = input("  Remove downloads/ directory? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            shutil.rmtree(downloads_dir)
            print("  ✓ Removed downloads/ directory")
        else:
            print("  ⊙ Kept downloads/ directory")
    else:
        print("  ⊙ downloads/ directory not found")


def remove_venv():
    """Remove virtual environment"""
    print("\nRemoving virtual environment...")
    
    venv_dir = Path("venv")
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        print("  ✓ Removed venv/ directory")
    else:
        print("  ⊙ venv/ directory not found")


def remove_pycache():
    """Remove Python cache directories"""
    print("\nRemoving Python cache files...")
    
    count = 0
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
        count += 1
    
    if count > 0:
        print(f"  ✓ Removed {count} __pycache__ directories")
    else:
        print("  ⊙ No cache directories found")


def main():
    """Main uninstallation process"""
    try:
        print_banner()
        
        # Check for --fresh flag
        fresh_install = "--fresh" in sys.argv
        
        if fresh_install:
            print("🔄 Fresh install mode: Will remove data directories\n")
        
        # Confirm uninstallation
        if not confirm_uninstall():
            print("\n⊘ Uninstallation cancelled")
            sys.exit(0)
        
        print_section("Uninstalling")
        
        # Remove components
        remove_config()
        remove_databases()
        remove_logs()
        remove_pycache()
        
        if fresh_install:
            remove_data_directory()
            remove_venv()
        
        # Ask about downloads
        remove_downloads()
        
        print_section("Uninstallation Complete")
        print("✓ Application data has been removed\n")
        
        if not fresh_install:
            print("Note: Virtual environment (venv/) was preserved.")
            print("To remove it, run: rm -rf venv/\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Uninstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Uninstallation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
