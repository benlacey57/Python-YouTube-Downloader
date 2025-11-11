#!/usr/bin/env python3
"""
Database Seeding Script

Seeds the database with initial data from JSON files.
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table

from managers.monitor_manager import MonitorManager
from managers.config_manager import ConfigManager
from managers.proxy_manager import ProxyManager
from utils.database_seeder import DatabaseSeeder
from models.channel import Channel

console = Console()


def seed_channels_callback(record: dict):
    """Callback to insert a channel record"""
    monitor_manager = MonitorManager()
    
    existing = monitor_manager.get_channel_by_url(record['url'])
    if existing:
        return "skipped"
    
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
    
    Path(channel.output_dir).mkdir(parents=True, exist_ok=True)
    monitor_manager.add_channel(channel)
    return "success"


def seed_proxies_callback(record: dict):
    """Callback to insert a proxy record"""
    config_manager = ConfigManager()
    
    # Format proxy string
    protocol = record.get('protocol', 'http')
    ip = record['ip']
    port = record['port']
    proxy_string = f"{protocol}://{ip}:{port}"
    
    # Check if already exists
    if proxy_string in config_manager.config.proxies:
        return "skipped"
    
    # Add proxy
    config_manager.config.proxies.append(proxy_string)
    config_manager.save_config()
    
    return "success"


def seed_config_preset_callback(record: dict):
    """Callback to apply a config preset"""
    config_manager = ConfigManager()
    
    console.print(f"\n[cyan]Available preset: {record['name']}[/cyan]")
    console.print(f"[dim]{record['description']}[/dim]")
    
    if not Confirm.ask("Apply this preset?", default=False):
        return "skipped"
    
    # Apply preset settings
    if record.get('video_quality'):
        config_manager.config.default_video_quality = record['video_quality']
    if record.get('audio_quality'):
        config_manager.config.default_audio_quality = record['audio_quality']
    if record.get('max_workers'):
        config_manager.config.max_workers = record['max_workers']
    if record.get('max_downloads_per_hour'):
        config_manager.config.max_downloads_per_hour = record['max_downloads_per_hour']
    if record.get('min_delay_seconds'):
        config_manager.config.min_delay_seconds = record['min_delay_seconds']
    if record.get('max_delay_seconds'):
        config_manager.config.max_delay_seconds = record['max_delay_seconds']
    if record.get('bandwidth_limit_mbps') is not None:
        config_manager.config.bandwidth_limit_mbps = record['bandwidth_limit_mbps']
    if record.get('normalize_filenames') is not None:
        config_manager.config.normalize_filenames = record['normalize_filenames']
    if record.get('filename_template'):
        config_manager.config.default_filename_template = record['filename_template']
    
    config_manager.save_config()
    
    return "success"


def list_available_seeds():
    """List all available seed files"""
    seeder = DatabaseSeeder()
    seeder.display_seed_files_table()


def validate_all_seeds():
    """Validate all seed files"""
    console.print("\n[bold cyan]Validating All Seed Files[/bold cyan]\n")
    
    seeder = DatabaseSeeder()
    
    validations = {
        'channels': ['url', 'title', 'is_monitored', 'check_interval_minutes',
                    'format_type', 'quality', 'output_dir', 'filename_template',
                    'download_order', 'enabled'],
        'proxies': ['ip', 'port', 'protocol'],
        'config_presets': ['name', 'description'],
        'filename_templates': ['name', 'template', 'description'],
        'playlists': ['title', 'url', 'category'],
        'storage_templates': ['name', 'provider_type', 'description']
    }
    
    all_valid = True
    
    for seed_name, required_fields in validations.items():
        console.print(f"\n[cyan]Validating {seed_name}.json...[/cyan]")
        valid = seeder.validate_seed_file(seed_name, {seed_name: required_fields})
        if not valid:
            all_valid = False
    
    if all_valid:
        console.print("\n[bold green]✓ All seed files are valid[/bold green]")
    else:
        console.print("\n[bold red]✗ Some seed files have errors[/bold red]")
    
    return all_valid


def seed_interactive():
    """Interactive seeding menu"""
    console.clear()
    
    header = Panel(
        "[bold cyan]Database Seeding Tool[/bold cyan]\n"
        "Select which data to seed",
        border_style="cyan"
    )
    console.print(header)
    
    options = [
        ("1", "Seed Channels", "channels", seed_channels_callback),
        ("2", "Seed Proxies", "proxies", seed_proxies_callback),
        ("3", "Apply Config Preset", "config_presets", seed_config_preset_callback),
        ("4", "List All Available Seeds", None, None),
        ("5", "Validate All Seeds", None, None),
        ("6", "Seed Everything", None, None),
        ("7", "Exit", None, None)
    ]
    
    for num, desc, *_ in options:
        console.print(f"  {num}. {desc}")
    
    choice = Prompt.ask("\nSelect option", choices=[o[0] for o in options], default="7")
    
    if choice == "4":
        list_available_seeds()
        input("\nPress Enter to continue...")
        return seed_interactive()
    
    elif choice == "5":
        validate_all_seeds()
        input("\nPress Enter to continue...")
        return seed_interactive()
    
    elif choice == "6":
        seed_all()
        return
    
    elif choice == "7":
        return
    
    else:
        # Seed specific type
        for num, desc, seed_name, callback in options:
            if num == choice and seed_name:
                seeder = DatabaseSeeder()
                seeder.seed_from_json(seed_name, {seed_name: callback})
                input("\nPress Enter to continue...")
                return seed_interactive()


def seed_all():
    """Seed all available seed files"""
    console.print("\n[bold cyan]Seeding All Data[/bold cyan]\n")
    
    if not Confirm.ask("This will seed channels, proxies, and config. Continue?", default=True):
        return
    
    seeder = DatabaseSeeder()
    
    # Seed channels
    console.print("\n[bold]Seeding Channels...[/bold]")
    seeder.seed_from_json('channels', {'channels': seed_channels_callback})
    
    # Seed proxies
    console.print("\n[bold]Seeding Proxies...[/bold]")
    seeder.seed_from_json('proxies', {'proxies': seed_proxies_callback})
    
    console.print("\n[bold green]✓ All seeding completed![/bold green]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Database Seeding Tool')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode - choose what to seed')
    parser.add_argument('--channels', action='store_true',
                       help='Seed channels only')
    parser.add_argument('--proxies', action='store_true',
                       help='Seed proxies only')
    parser.add_argument('--all', action='store_true',
                       help='Seed everything')
    parser.add_argument('--list', action='store_true',
                       help='List available seed files')
    parser.add_argument('--validate', action='store_true',
                       help='Validate all seed files')
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_available_seeds()
        elif args.validate:
            validate_all_seeds()
        elif args.channels:
            seeder = DatabaseSeeder()
            seeder.seed_from_json('channels', {'channels': seed_channels_callback})
        elif args.proxies:
            seeder = DatabaseSeeder()
            seeder.seed_from_json('proxies', {'proxies': seed_proxies_callback})
        elif args.all:
            seed_all()
        elif args.interactive:
            seed_interactive()
        else:
            # Default to interactive
            seed_interactive()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
