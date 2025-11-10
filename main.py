#!/usr/bin/env python3
"""
Playlist Downloader - Main application entry point
Advanced video/audio playlist management with monitoring and statistics
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

# Import managers
from managers.database_manager import DatabaseManager
from managers.config_manager import ConfigManager
from managers.stats_manager import StatsManager
from managers.queue_manager import QueueManager
from managers.monitor_manager import MonitorManager
from managers.proxy_manager import ProxyManager

# Import downloaders
from downloaders.playlist_downloader import PlaylistDownloader

# Import notifiers
from notifiers.slack_notifier import SlackNotifier

# Import UI
from ui.menu import Menu
from ui.settings_menu import SettingsMenu
from ui.monitoring_menu import MonitoringMenu
from ui.stats_display import StatsDisplay

# Import models
from models.channel import Channel
from models.download_item import DownloadItem

# Import enums
from enums import DownloadStatus, DownloadFormat

console = Console()


def initialize_application():
    """Initialize application and database"""
    console.print("[cyan]Initializing Playlist Downloader...[/cyan]")
    
    # Initialize database
    db_manager = DatabaseManager()
    if not db_manager.connect():
        console.print("[red]Failed to connect to database[/red]")
        sys.exit(1)
    
    if not db_manager.create_tables():
        console.print("[red]Failed to create database tables[/red]")
        sys.exit(1)
    
    console.print("[green]✓ Database initialized[/green]")
    
    # Initialize managers
    config_manager = ConfigManager()
    stats_manager = StatsManager(db_manager)
    queue_manager = QueueManager(db_manager, stats_manager)
    monitor_manager = MonitorManager(db_manager)
    
    # Initialize notifier
    slack_notifier = SlackNotifier(config_manager.config.slack_webhook_url)
    
    # Initialize downloader
    downloader = PlaylistDownloader(
        config_manager.config,
        stats_manager,
        slack_notifier
    )
    
    # Load proxies if available
    proxy_manager = ProxyManager()
    if proxy_manager.load_proxies_from_file():
        config_manager.config.proxies = proxy_manager.proxies
        config_manager.save_config()
    
    console.print("[green]✓ Application initialized[/green]\n")
    
    return {
        'db_manager': db_manager,
        'config_manager': config_manager,
        'stats_manager': stats_manager,
        'queue_manager': queue_manager,
        'monitor_manager': monitor_manager,
        'proxy_manager': proxy_manager,
        'slack_notifier': slack_notifier,
        'downloader': downloader
    }


def extract_channel_from_playlist(playlist_info):
    """Extract channel information from playlist info"""
    channel_url = playlist_info.get('channel_url', '')
    uploader = playlist_info.get('uploader', '')
    uploader_url = playlist_info.get('uploader_url', '')
    
    # Prefer channel_url, fallback to uploader_url
    if channel_url:
        return channel_url, uploader
    elif uploader_url:
        return uploader_url, uploader
    
    return None, uploader


def handle_download_new_playlist(managers):
    """Handle downloading a new playlist"""
    downloader = managers['downloader']
    queue_manager = managers['queue_manager']
    monitor_manager = managers['monitor_manager']
    config_manager = managers['config_manager']
    
    playlist_url = Prompt.ask("\n[cyan]Enter playlist URL[/cyan]")
    
    console.print("\n[yellow]Fetching playlist information...[/yellow]")
    playlist_info = downloader.get_playlist_info(playlist_url)
    
    if not playlist_info:
        console.print("[red]Failed to fetch playlist information[/red]")
        console.print("[yellow]Tip: Configure authentication in Settings if needed[/yellow]")
        return
    
    playlist_title = playlist_info.get('title', 'Unknown Playlist')
    
    entries = playlist_info.get('entries')
    if entries is None:
        entries = []
    
    entries = [e for e in entries if e is not None]
    
    if not entries:
        console.print("[red]No entries found in playlist[/red]")
        return
    
    info_panel = Panel(
        f"[green]Playlist:[/green] {playlist_title}\n"
        f"[green]Total items:[/green] {len(entries)}",
        title="[bold]Playlist Info[/bold]",
        border_style="green"
    )
    console.print("\n")
    console.print(info_panel)
    
    # Ask for download limit if large playlist
    if len(entries) > 50:
        if Confirm.ask(f"\nLimit downloads from {len(entries)} items?"):
            limit = IntPrompt.ask("How many items to download?", default=50)
            entries = entries[:limit]
    
    # Format selection
    format_choice = Prompt.ask(
        "\nDownload format",
        choices=["video", "audio"],
        default="video"
    )
    format_type = DownloadFormat.VIDEO.value if format_choice == "video" else DownloadFormat.AUDIO.value
    
    if format_type == DownloadFormat.AUDIO.value:
        if not downloader.check_ffmpeg():
            console.print("[red]Cannot proceed without FFmpeg[/red]")
            return
    
    # Quality selection
    quality = get_quality_choice(format_type)
    
    # Download order
    download_order = get_download_order()
    
    # Filename template
    use_template = Confirm.ask(
        f"\nUse filename template? (default: {config_manager.config.default_filename_template})",
        default=True
    )
    filename_template = config_manager.config.default_filename_template if use_template else None
    
    # Output directory
    default_dir = f"downloads/{playlist_title}"
    output_dir = Prompt.ask("\nOutput directory", default=default_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Extract channel information
    channel_url, uploader = extract_channel_from_playlist(playlist_info)
    channel_id = None
    
    if channel_url:
        # Check if channel exists
        existing_channel = monitor_manager.get_channel_by_url(channel_url)
        
        if existing_channel:
            channel_id = existing_channel.id
        else:
            # Create new channel
            channel = Channel(
                id=None,
                url=channel_url,
                title=uploader or playlist_title,
                is_monitored=False,
                format_type=format_type,
                quality=quality,
                output_dir=output_dir,
                filename_template=filename_template,
                download_order=download_order
            )
            channel_id = monitor_manager.add_channel(channel)
    
    # Create download items
    items = []
    for entry in entries:
        if not entry:
            continue
        
        url = entry.get('url', '')
        title = entry.get('title', 'Unknown')
        
        if not url:
            continue
        
        items.append({
            'url': url,
            'title': title,
            'upload_date': entry.get('upload_date'),
            'uploader': entry.get('uploader'),
            'video_id': entry.get('id')
        })
    
    if not items:
        console.print("[red]No valid items found[/red]")
        return
    
    console.print(f"\n[cyan]Prepared {len(items)} items for download[/cyan]")
    
    # Create queue
    queue_id = queue_manager.create_queue(
        channel_id=channel_id,
        playlist_url=playlist_url,
        playlist_title=playlist_title,
        format_type=format_type,
        quality=quality,
        output_dir=output_dir,
        items=items,
        download_order=download_order,
        filename_template=filename_template
    )
    
    console.print(f"\n[green]✓ Queue created:[/green] {queue_id}")
    
    if Confirm.ask("\nStart download now?", default=True):
        queue = queue_manager.get_queue(queue_id)
        downloader.download_queue(queue, queue_manager)


def handle_resume_download(managers):
    """Handle resuming incomplete downloads"""
    queue_manager = managers['queue_manager']
    downloader = managers['downloader']
    
    incomplete = queue_manager.list_incomplete_queues()
    
    if not incomplete:
        console.print("\n[yellow]No incomplete queues found[/yellow]")
        return
    
    console.print("\n")
    queue_table = Table(title="Incomplete Queues")
    queue_table.add_column("#", style="cyan")
    queue_table.add_column("Playlist", style="magenta")
    queue_table.add_column("Pending", style="yellow", justify="right")
    queue_table.add_column("Failed", style="red", justify="right")
    
    for idx, queue in enumerate(incomplete, 1):
        items = queue_manager.get_queue_items(queue.id)
        pending = sum(1 for item in items if item.status == DownloadStatus.PENDING.value)
        failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
        queue_table.add_row(str(idx), queue.playlist_title[:40], str(pending), str(failed))
    
    console.print(queue_table)
    
    selection = IntPrompt.ask(
        "\nSelect queue",
        default=1,
        choices=[str(i) for i in range(1, len(incomplete) + 1)]
    )
    
    queue = incomplete[selection - 1]
    
    if Confirm.ask("\nRestart downloads?", default=True):
        downloader.download_queue(queue, queue_manager)


def handle_search_channel(managers):
    """Handle searching channel for playlists"""
    downloader = managers['downloader']
    
    channel_url = Prompt.ask("\n[cyan]Enter channel URL[/cyan]")
    
    console.print("\n[yellow]Searching for playlists...[/yellow]")
    playlists = downloader.search_channel_playlists(channel_url)
    
    if not playlists:
        console.print("[red]No playlists found[/red]")
        return
    
    console.print(f"\n[green]Found {len(playlists)} playlists:[/green]\n")
    for idx, playlist in enumerate(playlists, 1):
        count = playlist.get('playlist_count', 'Unknown')
        console.print(f"  {idx}. {playlist['title']} ({count} items)")
    
    if playlists:
        selection = IntPrompt.ask(
            "\nSelect playlist (0 to cancel)",
            default=0
        )
        
        if selection > 0 and selection <= len(playlists):
            selected = playlists[selection - 1]
            info_panel = Panel(
                f"[cyan]Title:[/cyan] {selected['title']}\n"
                f"[cyan]URL:[/cyan] {selected['url']}",
                title="[bold]Selected Playlist[/bold]",
                border_style="green"
            )
            console.print("\n")
            console.print(info_panel)
            console.print("\n[yellow]Use option 1 from main menu to download this playlist[/yellow]")


def handle_view_queue_status(managers):
    """Handle viewing queue status"""
    queue_manager = managers['queue_manager']
    monitor_manager = managers['monitor_manager']
    stats_manager = managers['stats_manager']
    db_manager = managers['db_manager']
    
    # Show dashboard
    dashboard = StatsDisplay.display_dashboard(queue_manager, monitor_manager, stats_manager)
    console.print("\n")
    console.print(dashboard)
    
    # Show detailed queue table
    rows = db_manager.fetch_all("SELECT * FROM queues ORDER BY created_at DESC")
    
    if not rows:
        console.print("\n[yellow]No queues found[/yellow]")
        return
    
    from models.queue import Queue
    
    table = Table(title="\nDownload Queues", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan")
    table.add_column("Playlist", style="magenta")
    table.add_column("Format", style="yellow")
    table.add_column("✓", style="green", justify="right")
    table.add_column("✗", style="red", justify="right")
    table.add_column("Total", style="blue", justify="right")
    table.add_column("Time", style="white")
    
    for row in rows:
        queue = Queue.from_row(tuple(row))
        items = queue_manager.get_queue_items(queue.id)
        
        completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
        failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
        
        # Calculate total time
        total_time = sum(
            item.download_duration_seconds or 0
            for item in items
        )
        
        from downloaders.playlist_downloader import PlaylistDownloader
        time_str = PlaylistDownloader(managers['config_manager'].config)._format_duration(total_time) if total_time > 0 else "N/A"
        
        table.add_row(
            queue.id[:8],
            queue.playlist_title[:35],
            queue.format_type,
            str(completed),
            str(failed),
            str(len(items)),
            time_str
        )
    
    console.print("\n")
    console.print(table)


def handle_settings(managers):
    """Handle settings menu"""
    config_manager = managers['config_manager']
    proxy_manager = managers['proxy_manager']
    slack_notifier = managers['slack_notifier']
    
    while True:
        choice = SettingsMenu.display_settings_menu(config_manager)
        
        if choice == "1":
            config_manager.configure_authentication()
        elif choice == "2":
            handle_proxy_management(proxy_manager, config_manager)
        elif choice == "3":
            config_manager.configure_workers()
        elif choice == "4":
            config_manager.configure_filename_template()
        elif choice == "5":
            config_manager.configure_slack()
            # Update slack notifier
            slack_notifier.webhook_url = config_manager.config.slack_webhook_url
        elif choice == "6":
            config_manager.configure_timeout()
        elif choice == "7":
            config_manager.configure_alert_thresholds()
        elif choice == "8":
            break
    
    # Refresh downloader with updated config
    managers['downloader'] = PlaylistDownloader(
        config_manager.config,
        managers['stats_manager'],
        slack_notifier
    )


def handle_proxy_management(proxy_manager, config_manager):
    """Handle proxy management submenu"""
    console.print("\n[cyan]Proxy Management[/cyan]")
    
    if proxy_manager.proxies:
        console.print(f"\n[green]Current proxies: {len(proxy_manager.proxies)}[/green]")
        for idx, proxy in enumerate(proxy_manager.proxies[:10], 1):
            console.print(f"  {idx}. {proxy}")
        if len(proxy_manager.proxies) > 10:
            console.print(f"  ... and {len(proxy_manager.proxies) - 10} more")
    else:
        console.print("\n[yellow]No proxies configured[/yellow]")
        console.print("\nTo use proxies, create one of these files:")
        console.print("  • proxies.txt (one proxy per line)")
        console.print("  • proxies.csv (proxy,description format)\n")
    
    options = [
        ("1", "Reload proxies from file"),
        ("2", "Validate all proxies"),
        ("3", "Remove non-working proxies"),
        ("4", "Back")
    ]
    
    option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
    console.print(f"\n{option_text}\n")
    
    choice = Prompt.ask("Select option", choices=[num for num, _ in options], default="4")
    
    if choice == "1":
        if proxy_manager.load_proxies_from_file():
            config_manager.config.proxies = proxy_manager.proxies
            config_manager.save_config()
    elif choice == "2":
        timeout = IntPrompt.ask("Proxy timeout (seconds)", default=10)
        workers = IntPrompt.ask("Concurrent validation workers", default=5)
        proxy_manager.validate_all_proxies(timeout, workers)
    elif choice == "3":
        if not proxy_manager.working_proxies:
            console.print("\n[yellow]Run validation first (option 2)[/yellow]")
        else:
            proxy_manager.remove_dead_proxies()
            config_manager.config.proxies = proxy_manager.proxies
            config_manager.save_config()


def handle_monitoring(managers):
    """Handle monitoring menu"""
    monitor_manager = managers['monitor_manager']
    downloader = managers['downloader']
    queue_manager = managers['queue_manager']
    config_manager = managers['config_manager']
    slack_notifier = managers['slack_notifier']
    
    def check_callback(channels):
        """Callback for monitoring check"""
        for channel in channels:
            try:
                playlist_info = downloader.get_playlist_info(channel.url)
                if not playlist_info:
                    continue
                
                entries = playlist_info.get('entries', [])
                if not entries:
                    continue
                
                # Filter for new videos
                new_videos = []
                for entry in entries:
                    if not entry:
                        continue
                    
                    upload_date = entry.get('upload_date')
                    if channel.last_video_date and upload_date:
                        if upload_date <= channel.last_video_date:
                            continue
                    
                    new_videos.append(entry)
                
                if new_videos:
                    # Create download items
                    items = []
                    for entry in new_videos:
                        items.append({
                            'url': entry.get('url', ''),
                            'title': entry.get('title', 'Unknown'),
                            'upload_date': entry.get('upload_date'),
                            'uploader': entry.get('uploader'),
                            'video_id': entry.get('id')
                        })
                    
                    # Create queue
                    queue_id = queue_manager.create_queue(
                        channel_id=channel.id,
                        playlist_url=channel.url,
                        playlist_title=channel.title,
                        format_type=channel.format_type,
                        quality=channel.quality,
                        output_dir=channel.output_dir,
                        items=items,
                        download_order=channel.download_order,
                        filename_template=channel.filename_template
                    )
                    
                    queue = queue_manager.get_queue(queue_id)
                    
                    # Mark as monitored
                    from models.queue import Queue
                    queue_obj = Queue(
                        id=queue.id,
                        channel_id=queue.channel_id,
                        playlist_url=queue.playlist_url,
                        playlist_title=queue.playlist_title,
                        format_type=queue.format_type,
                        quality=queue.quality,
                        output_dir=queue.output_dir,
                        download_order=queue.download_order,
                        filename_template=queue.filename_template,
                        is_monitored=True,
                        created_at=queue.created_at
                    )
                    
                    console.print(f"[green]✓ Found {len(new_videos)} new videos in {channel.title}[/green]")
                    
                    # Send Slack notification
                    if slack_notifier and slack_notifier.is_configured():
                        slack_notifier.notify_monitoring_update(channel.title, len(new_videos))
                    
                    # Download queue
                    downloader.download_queue(queue_obj, queue_manager)
                    
                    # Update channel
                    channel.last_checked = datetime.now().isoformat()
                    if new_videos:
                        latest_date = max(v.get('upload_date', '') for v in new_videos if v.get('upload_date'))
                        if latest_date:
                            channel.last_video_date = latest_date
                    
                    monitor_manager.update_channel(channel)
            
            except Exception as e:
                console.print(f"[red]Error checking {channel.title}: {e}[/red]")
    
    while True:
        choice = MonitoringMenu.display_monitoring_menu(
            monitor_manager, downloader, queue_manager, config_manager, slack_notifier
        )
        
        if choice == "1":
            MonitoringMenu.add_channel_to_monitoring(monitor_manager, downloader, config_manager)
        elif choice == "2":
            MonitoringMenu.remove_channel_from_monitoring(monitor_manager)
        elif choice == "3":
            monitor_manager.start_monitoring(check_callback)
        elif choice == "4":
            monitor_manager.stop_monitoring()
        elif choice == "5":
            console.print("\n[yellow]Checking for new videos...[/yellow]")
            channels = monitor_manager.get_monitored_channels()
            if channels:
                check_callback(channels)
            else:
                console.print("[yellow]No monitored channels[/yellow]")
        elif choice == "6":
            break


def get_quality_choice(format_type: str) -> str:
    """Get quality selection from user"""
    if format_type == DownloadFormat.AUDIO.value:
        return "192"
    
    console.print("\n[cyan]Video Quality Options:[/cyan]")
    qualities = ["best", "1080p", "720p", "480p", "360p", "worst"]
    
    for idx, quality in enumerate(qualities, 1):
        console.print(f"  {idx}. {quality}")
    
    choice = Prompt.ask(
        "Select quality",
        choices=[str(i) for i in range(1, len(qualities) + 1)],
        default="1"
    )
    
    return qualities[int(choice) - 1]


def get_download_order() -> str:
    """Get download order preference from user"""
    console.print("\n[cyan]Download Order:[/cyan]")
    orders = [
        ("original", "Original playlist order"),
        ("oldest_first", "Oldest to newest"),
        ("newest_first", "Newest to oldest")
    ]
    
    for idx, (value, description) in enumerate(orders, 1):
        console.print(f"  {idx}. {description}")
    
    choice = Prompt.ask(
        "Select order",
        choices=[str(i) for i in range(1, len(orders) + 1)],
        default="1"
    )
    
    return orders[int(choice) - 1][0]


def main():
    """Main application entry point"""
    try:
        # Initialize application
        managers = initialize_application()
        
        # Main loop
        while True:
            choice = Menu.display_main_menu()
            
            if choice == "1":
                handle_download_new_playlist(managers)
            elif choice == "2":
                handle_resume_download(managers)
            elif choice == "3":
                handle_search_channel(managers)
            elif choice == "4":
                handle_view_queue_status(managers)
            elif choice == "5":
                StatsDisplay.display_statistics(
                    managers['stats_manager'],
                    managers['queue_manager']
                )
            elif choice == "6":
                handle_monitoring(managers)
            elif choice == "7":
                handle_settings(managers)
            elif choice == "8":
                if managers['monitor_manager'].is_running:
                    managers['monitor_manager'].stop_monitoring()
                console.print("\n[cyan]Goodbye![/cyan]\n")
                managers['db_manager'].disconnect()
                break
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        if 'managers' in locals():
            if managers['monitor_manager'].is_running:
                managers['monitor_manager'].stop_monitoring()
            managers['db_manager'].disconnect()
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
