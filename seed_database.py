#!/usr/bin/env python3
"""
Database Seeding Script

Seeds the database with initial data from JSON files.
Run this script to populate the database with default channels and configurations.

Usage:
    python seed_database.py
    python seed_database.py --reset  # Delete all data first
    python seed_database.py --validate  # Validate seed files only
    python seed_database.py --info  # Show seed file information
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.table import Table

from managers.monitor_manager import MonitorManager
from utils.database_seeder import DatabaseSeeder
from models.channel import Channel

console = Console()


def seed_channels_callback(record: dict):
    """
    Callback to insert a channel record
    
    Args:
        record: Channel data dictionary
        
    Returns:
        str: "success" or "skipped"
    """
    monitor_manager = MonitorManager()
    
    # Check if channel already exists
    existing = monitor_manager.get_channel_by_url(record['url'])
    if existing:
        return "skipped"
    
    # Create channel from record
    channel = Channel(
        id=None,
        url=record['url'],
        title=record['title'],
        is_monitored=record.get('is_monitored', False),
        check_interval_minutes=record.get('check_interval_minutes', 60),
        format_type=record.get('format_type', 'video'),
        quality=record.get('quality', '720p'),
        output_dir=record.get('output_dir', f"downloads/{record['title']}"),
        filename_template=record.get('filename_template', '{index:03d} - {title}'),
        download_order=record.get('download_order', 'newest_first'),
        enabled=record.get('enabled', True)
    )
    
    # Create output directory
    Path(channel.output_dir).mkdir(parents=True, exist_ok=True)
    
    monitor_manager.add_channel(channel)
    return "success"


def validate_seed_files():
    """Validate all seed files"""
    console.print("\n[bold cyan]Validating Seed Files[/bold cyan]\n")
    
    seeder = DatabaseSeeder()
    
    # Define required fields for each table
    required_fields = {
        'channels': [
            'url', 'title', 'is_monitored', 'check_interval_minutes',
            'format_type', 'quality', 'output_dir', 'filename_template',
            'download_order', 'enabled'
        ]
    }
    
    # Validate channels seed file
    valid = seeder.validate_seed_file('channels', required_fields)
    
    return valid


def show_seed_info():
    """Display information about available seed files"""
    console.print("\n[bold cyan]Available Seed Files[/bold cyan]\n")
    
    seeds_dir = Path("seeds")
    
    if not seeds_dir.exists():
        console.print("[yellow]Seeds directory not found[/yellow]")
        return
    
    json_files = list(seeds_dir.glob("*.json"))
    
    if not json_files:
        console.print("[yellow]No seed files found[/yellow]")
        return
    
    table = Table(show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Records", style="yellow")
    table.add_column("Tables", style="magenta")
    
    import json
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            total_records = sum(len(records) for records in data.values())
            size_kb = json_file.stat().st_size / 1024
            table_names = ', '.join(data.keys())
            
            table.add_row(
                json_file.name,
                f"{size_kb:.1f} KB",
                str(total_records),
                table_names
            )
        except Exception as e:
            table.add_row(json_file.name, "Error", "?", str(e)[:20])
    
    console.print(table)


def reset_database():
    """Reset (delete all data from) the database"""
    console.print("\n[bold red]Reset Database[/bold red]\n")
    
    console.print("[yellow]This will delete ALL data from the database:[/yellow]")
    console.print("  • All channels")
    console.print("  • All monitoring history")
    console.print("  • All check records")
    
    if not Confirm.ask("\n[red]Are you sure? This CANNOT be undone![/red]", default=False):
        console.print("[yellow]Reset cancelled[/yellow]")
        return False
    
    if not Confirm.ask("[red]Type yes to confirm:[/red]", default=False):
        console.print("[yellow]Reset cancelled[/yellow]")
        return False
    
    monitor_manager = MonitorManager()
    
    # Delete all channels
    channels = monitor_manager.get_all_channels()
    
    console.print(f"\n[yellow]Deleting {len(channels)} channels...[/yellow]")
    
    for channel in channels:
        monitor_manager.delete_channel(channel.id)
    
    console.print(f"[green]✓ Deleted {len(channels)} channels[/green]")
    
    return True


def seed_database(reset: bool = False):
    """
    Seed the database with initial data
    
    Args:
        reset: Whether to reset the database first
    """
    console.clear()
    
    header = Panel(
        "[bold cyan]Database Seeding Tool[/bold cyan]\n"
        "Populates the database with initial channel data",
        border_style="cyan"
    )
    console.print(header)
    
    # Show current state
    monitor_manager = MonitorManager()
    existing_channels = monitor_manager.get_all_channels()
    
    if existing_channels:
        console.print(f"\n[yellow]Current database state:[/yellow]")
        console.print(f"  • {len(existing_channels)} channels exist")
        
        monitored = [c for c in existing_channels if c.is_monitored]
        console.print(f"  • {len(monitored)} are monitored")
    
    # Reset if requested
    if reset:
        if not reset_database():
            return
    
    # Validate seed files
    console.print("\n[cyan]Validating seed files...[/cyan]")
    if not validate_seed_files():
        console.print("\n[red]Validation failed. Please fix the seed files.[/red]")
        return
    
    # Confirm seeding
    if existing_channels and not reset:
        console.print("\n[yellow]Note: Existing channels will be skipped[/yellow]")
    
    if not Confirm.ask("\nProceed with seeding?", default=True):
        console.print("[yellow]Seeding cancelled[/yellow]")
        return
    
    # Perform seeding
    console.print("\n[bold cyan]Starting Database Seeding[/bold cyan]\n")
    
    seeder = DatabaseSeeder()
    
    seed_configs = {
        'channels': seed_channels_callback
    }
    
    seeder.seed_from_json('channels', seed_configs)
    
    # Show final state with categories
    console.print("\n[bold green]Seeding Complete![/bold green]\n")
    
    all_channels = monitor_manager.get_all_channels()
    monitored_channels = [c for c in all_channels if c.is_monitored]
    
    # Categorize channels
    dev_channels = [c for c in all_channels if 'Development' in c.output_dir]
    crime_channels = [c for c in all_channels if 'True_Crime' in c.output_dir]
    comedy_channels = [c for c in all_channels if 'Comedy' in c.output_dir]
    news_channels = [c for c in all_channels if 'News' in c.output_dir]
    
    summary_table = Table(title="Database Summary", show_header=True)
    summary_table.add_column("Category", style="cyan")
    summary_table.add_column("Total", justify="right", style="white")
    summary_table.add_column("Monitored", justify="right", style="green")
    
    summary_table.add_row("Development", str(len(dev_channels)), 
                          str(len([c for c in dev_channels if c.is_monitored])))
    summary_table.add_row("True Crime", str(len(crime_channels)), 
                          str(len([c for c in crime_channels if c.is_monitored])))
    summary_table.add_row("Comedy", str(len(comedy_channels)), 
                          str(len([c for c in comedy_channels if c.is_monitored])))
    summary_table.add_row("News", str(len(news_channels)), 
                          str(len([c for c in news_channels if c.is_monitored])))
    summary_table.add_row("[bold]Total[/bold]", f"[bold]{len(all_channels)}[/bold]", 
                          f"[bold]{len(monitored_channels)}[/bold]")
    
    console.print(summary_table)
    
    if monitored_channels:
        console.print("\n[cyan]Monitored Channels:[/cyan]")
        for channel in monitored_channels:
            check_interval_hours = channel.check_interval_minutes / 60
            console.print(f"  • {channel.title} ({channel.quality}, every {check_interval_hours:.0f}h)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Database Seeding Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed_database.py              Seed the database
  python seed_database.py --reset      Delete all data and seed
  python seed_database.py --validate   Validate seed files only
  python seed_database.py --info       Show seed file information
        """
    )
    
    parser.add_argument('--reset', action='store_true',
                       help='Delete all existing data before seeding')
    parser.add_argument('--validate', action='store_true',
                       help='Only validate seed files, do not seed')
    parser.add_argument('--info', action='store_true',
                       help='Show information about available seed files')
    
    args = parser.parse_args()
    
    try:
        if args.info:
            show_seed_info()
        elif args.validate:
            validate_seed_files()
        else:
            seed_database(reset=args.reset)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
