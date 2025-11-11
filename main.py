"""Main application entry point"""
from managers.config_manager import ConfigManager
from managers.queue_manager import QueueManager
from managers.stats_manager import StatsManager
from managers.proxy_manager import ProxyManager
from managers.monitor_manager import MonitorManager
from downloaders.playlist_downloader import PlaylistDownloader
from notifiers.slack_notifier import SlackNotifier
from ui.menu import Menu
from ui.settings_menu import SettingsMenu
from ui.monitoring_menu import MonitoringMenu
from ui.storage_menu import StorageMenu
from ui.setup_wizard import SetupWizard, StatusPage
from utils.storage_providers import StorageManager
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from pathlib import Path
import sys

console = Console()


def main():
    """Main application loop"""
    console.clear()
    
    # Initialize managers
    config_manager = ConfigManager()
    queue_manager = QueueManager()
    stats_manager = StatsManager()
    proxy_manager = ProxyManager(config_manager.config.proxies)
    slack_notifier = SlackNotifier(config_manager.config.slack_webhook_url)
    monitor_manager = MonitorManager()
    storage_manager = StorageManager()
    
    # Initialize downloader
    downloader = PlaylistDownloader(
        config_manager.config,
        stats_manager,
        slack_notifier
    )
    
    # Run setup wizard if not completed
    if not config_manager.config.setup_completed:
        SetupWizard.run(config_manager)
        console.clear()
    
    # Load proxies if configured
    if config_manager.config.proxies:
        proxy_manager.proxies = config_manager.config.proxies
    
    # Main menu loop
    while True:
        choice = Menu.display_main_menu()
        
        if choice == "1":
            handle_new_download(downloader, queue_manager, config_manager, storage_manager)
        elif choice == "2":
            handle_resume_download(downloader, queue_manager, config_manager)
        elif choice == "3":
            handle_channel_search(downloader)
        elif choice == "4":
            handle_view_queue(queue_manager)
        elif choice == "5":
            handle_view_stats(stats_manager)
        elif choice == "6":
            handle_monitoring(monitor_manager, downloader, queue_manager, 
                            config_manager, slack_notifier)
        elif choice == "7":
            handle_settings(config_manager, proxy_manager, storage_manager, 
                          stats_manager, queue_manager)
        elif choice == "8":
            console.print("\n[cyan]Goodbye![/cyan]")
            break


def handle_settings(config_manager, proxy_manager, storage_manager, stats_manager, queue_manager):
    """Handle settings submenu"""
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
        elif choice == "6":
            config_manager.configure_timeout()
        elif choice == "7":
            config_manager.configure_alert_thresholds()
        elif choice == "8":
            config_manager.configure_rate_limiting()
        elif choice == "9":
            config_manager.configure_bandwidth_limit()
        elif choice == "10":
            config_manager.configure_live_streams()
        elif choice == "11":
            config_manager.configure_default_quality()
        elif choice == "12":
            config_manager.configure_filename_normalization()
        elif choice == "13":
            handle_storage_management(config_manager, storage_manager)
        elif choice == "14":
            StatusPage.display(config_manager, storage_manager, proxy_manager, stats_manager)
        elif choice == "15":
            break


def handle_storage_management(config_manager, storage_manager):
    """Handle storage management submenu"""
    while True:
        choice = StorageMenu.display_storage_menu(config_manager, storage_manager)
        
        if choice == "1":
            StorageMenu.add_ftp_storage(config_manager)
        elif choice == "2":
            StorageMenu.add_sftp_storage(config_manager)
        elif choice == "3":
            StorageMenu.add_google_drive_storage(config_manager)
        elif choice == "4":
            StorageMenu.add_dropbox_storage(config_manager)
        elif choice == "5":
            StorageMenu.add_onedrive_storage(config_manager)
        elif choice == "6":
            StorageMenu.configure_storage_provider(config_manager)
        elif choice == "7":
            StorageMenu.remove_storage_provider(config_manager)
        elif choice == "8":
            StorageMenu.set_default_storage(config_manager)
        elif choice == "9":
            StorageMenu.test_storage_connections(config_manager, storage_manager)
        elif choice == "10":
            break


def handle_new_download(downloader, queue_manager, config_manager, storage_manager):
    """Handle new playlist download"""
    console.print("\n[cyan]Download New Playlist[/cyan]")
    
    playlist_url = Prompt.ask("\nPlaylist URL")
    
    console.print("\n[yellow]Fetching playlist information...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]")
    
    playlist_info = downloader.get_playlist_info(playlist_url)
    
    if not playlist_info:
        console.print("[red]Failed to fetch playlist information[/red]")
        console.print("\n[yellow]Troubleshooting tips:[/yellow]")
        console.print("  1. Check the URL is correct")
        console.print("  2. Try configuring authentication in Settings")
        console.print("  3. Check your internet connection")
        console.print("  4. Try using a different proxy (if enabled)")
        input("\nPress Enter to continue...")
        return
    
    playlist_title = playlist_info.get('title', 'Unknown Playlist')
    entry_count = len(playlist_info.get('entries', []))
    
    console.print(f"\n[green]Found playlist:[/green] {playlist_title}")
    console.print(f"[cyan]Videos:[/cyan] {entry_count}")
    
    # Format selection
    format_choice = Prompt.ask(
        "\nDownload format",
        choices=["video", "audio"],
        default="video"
    )
    
    # Quality selection (with defaults and overrides)
    if format_choice == "video":
        console.print(f"\n[cyan]Default video quality:[/cyan] {config_manager.config.default_video_quality}")
        if Confirm.ask("Use default quality?", default=True):
            quality = config_manager.config.default_video_quality
        else:
            console.print("\n[cyan]Video Quality Options:[/cyan]")
            qualities = ["best", "1080p", "720p", "480p", "360p", "worst"]
            for idx, q in enumerate(qualities, 1):
                console.print(f"  {idx}. {q}")
            
            choice = Prompt.ask(
                "Select quality",
                choices=[str(i) for i in range(1, len(qualities) + 1)],
                default="3"
            )
            quality = qualities[int(choice) - 1]
    else:
        console.print(f"\n[cyan]Default audio quality:[/cyan] {config_manager.config.default_audio_quality}kbps")
        if Confirm.ask("Use default quality?", default=True):
            quality = config_manager.config.default_audio_quality
        else:
            quality = Prompt.ask("Audio quality (kbps)", default="192")
    
    # Storage selection
    storage_providers = ["local"] + config_manager.list_storage_providers()
    
    console.print(f"\n[cyan]Storage Providers:[/cyan]")
    for idx, provider in enumerate(storage_providers, 1):
        is_default = " (default)" if provider == config_manager.config.default_storage else ""
        console.print(f"  {idx}. {provider}{is_default}")
    
    storage_choice = Prompt.ask(
        "Select storage",
        choices=[str(i) for i in range(1, len(storage_providers) + 1)],
        default="1"
    )
    
    storage_provider = storage_providers[int(storage_choice) - 1]
    
    # Check for storage-specific quality overrides
    storage_video_quality = None
    storage_audio_quality = None
    
    if storage_provider != "local":
        storage_config = config_manager.get_storage_provider(storage_provider)
        if storage_config:
            if storage_config.video_quality:
                console.print(f"\n[yellow]Note: {storage_provider} has quality override: {storage_config.video_quality}[/yellow]")
                if Confirm.ask("Use storage quality override?", default=True):
                    storage_video_quality = storage_config.video_quality
            
            if storage_config.audio_quality:
                console.print(f"\n[yellow]Note: {storage_provider} has audio override: {storage_config.audio_quality}kbps[/yellow]")
                if Confirm.ask("Use storage audio override?", default=True):
                    storage_audio_quality = storage_config.audio_quality
    
    # Output directory
    default_dir = f"downloads/{playlist_title}"
    output_dir = Prompt.ask("Output directory", default=default_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Filename template
    use_template = Confirm.ask(
        f"Use filename template? (default: {config_manager.config.default_filename_template})",
        default=True
    )
    filename_template = config_manager.config.default_filename_template if use_template else None
    
    # Download order
    console.print("\n[cyan]Download Order:[/cyan]")
    orders = [
        ("original", "Original playlist order"),
        ("oldest_first", "Oldest to newest"),
        ("newest_first", "Newest to oldest")
    ]
    
    for idx, (value, description) in enumerate(orders, 1):
        console.print(f"  {idx}. {description}")
    
    order_choice = Prompt.ask(
        "Select order",
        choices=[str(i) for i in range(1, len(orders) + 1)],
        default="1"
    )
    
    download_order = orders[int(order_choice) - 1][0]
    
    # Create queue
    from models.queue import Queue
    
    queue = Queue(
        id=None,
        playlist_url=playlist_url,
        playlist_title=playlist_title,
        format_type=format_choice,
        quality=storage_video_quality or storage_audio_quality or quality,
        output_dir=output_dir,
        download_order=download_order,
        filename_template=filename_template,
        storage_provider=storage_provider,
        storage_video_quality=storage_video_quality,
        storage_audio_quality=storage_audio_quality
    )
    
    queue = queue_manager.create_queue(queue)
    
    # Add items to queue
    console.print(f"\n[yellow]Adding {entry_count} items to queue...[/yellow]")
    
    entries = playlist_info.get('entries', [])
    for entry in entries:
        if not entry:
            continue
        
        from models.download_item import DownloadItem
        from enums import DownloadStatus
        
        item = DownloadItem(
            id=None,
            queue_id=queue.id,
            url=entry.get('url', ''),
            title=entry.get('title', 'Unknown'),
            status=DownloadStatus.PENDING.value,
            uploader=entry.get('uploader'),
            upload_date=entry.get('upload_date'),
            video_id=entry.get('id')
        )
        
        queue_manager.add_item_to_queue(item)
    
    console.print(f"[green]✓ Queue created with {entry_count} items[/green]")
    
    # Start download
    if Confirm.ask("\nStart download now?", default=True):
        downloader.download_queue(queue, queue_manager)
    else:
        console.print("[yellow]Queue saved. Use 'Resume incomplete download' to start later.[/yellow]")
    
    input("\nPress Enter to continue...")

def handle_resume_download(downloader, queue_manager, config_manager):
    """Handle resuming incomplete downloads"""
    console.print("\n[cyan]Resume Incomplete Download[/cyan]")
    
    # Get incomplete queues
    incomplete_queues = queue_manager.get_incomplete_queues()
    
    if not incomplete_queues:
        console.print("\n[yellow]No incomplete downloads found[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    # Display incomplete queues
    from rich.table import Table
    
    table = Table(title="Incomplete Downloads", show_header=True)
    table.add_column("#", style="cyan", width=6)
    table.add_column("Playlist", style="white")
    table.add_column("Format", style="yellow")
    table.add_column("Items", style="green")
    table.add_column("Progress", style="magenta")
    table.add_column("Created", style="blue")
    
    for idx, queue in enumerate(incomplete_queues, 1):
        items = queue_manager.get_queue_items(queue.id)
        
        from enums import DownloadStatus
        completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
        pending = sum(1 for item in items if item.status == DownloadStatus.PENDING.value)
        failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
        
        total = len(items)
        progress = f"{completed}/{total}"
        if failed > 0:
            progress += f" ({failed} failed)"
        
        created_date = queue.created_at[:10] if queue.created_at else "Unknown"
        
        table.add_row(
            str(idx),
            queue.playlist_title[:40],
            queue.format_type,
            str(total),
            progress,
            created_date
        )
    
    console.print("\n")
    console.print(table)
    
    # Select queue
    selection = IntPrompt.ask(
        "\nSelect queue number (0 to cancel)",
        default=0
    )
    
    if selection > 0 and selection <= len(incomplete_queues):
        queue = incomplete_queues[selection - 1]
        
        # Show queue details
        items = queue_manager.get_queue_items(queue.id)
        
        from enums import DownloadStatus
        completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
        pending = sum(1 for item in items if item.status == DownloadStatus.PENDING.value)
        failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
        
        details_panel = Panel(
            f"[cyan]Playlist:[/cyan] {queue.playlist_title}\n"
            f"[cyan]Format:[/cyan] {queue.format_type}\n"
            f"[cyan]Quality:[/cyan] {queue.quality}\n"
            f"[cyan]Output:[/cyan] {queue.output_dir}\n"
            f"[cyan]Storage:[/cyan] {queue.storage_provider}\n\n"
            f"[green]Completed:[/green] {completed}\n"
            f"[yellow]Pending:[/yellow] {pending}\n"
            f"[red]Failed:[/red] {failed}",
            title="[bold]Queue Details[/bold]",
            border_style="cyan"
        )
        console.print("\n")
        console.print(details_panel)
        
        # Options
        console.print("\n[cyan]Options:[/cyan]")
        console.print("  1. Resume download (skip completed)")
        console.print("  2. Retry failed items only")
        console.print("  3. Re-download everything")
        console.print("  4. Delete queue")
        console.print("  5. Cancel")
        
        option = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
        
        if option == "1":
            # Resume normal download
            downloader.download_queue(queue, queue_manager)
        
        elif option == "2":
            # Retry failed only
            if failed == 0:
                console.print("\n[yellow]No failed items to retry[/yellow]")
            else:
                console.print(f"\n[yellow]Retrying {failed} failed items...[/yellow]")
                
                # Reset failed items to pending
                from enums import DownloadStatus
                for item in items:
                    if item.status == DownloadStatus.FAILED.value:
                        item.status = DownloadStatus.PENDING.value
                        item.error = None
                        queue_manager.update_item(item)
                
                downloader.download_queue(queue, queue_manager)
        
        elif option == "3":
            # Re-download everything
            if Confirm.ask("\nThis will re-download ALL items. Continue?", default=False):
                # Reset all items to pending
                from enums import DownloadStatus
                for item in items:
                    item.status = DownloadStatus.PENDING.value
                    item.error = None
                    item.file_path = None
                    item.file_size_bytes = None
                    item.file_hash = None
                    item.download_started_at = None
                    item.download_completed_at = None
                    item.download_duration_seconds = None
                    queue_manager.update_item(item)
                
                downloader.download_queue(queue, queue_manager)
        
        elif option == "4":
            # Delete queue
            if Confirm.ask(f"\nDelete queue '{queue.playlist_title}'?", default=False):
                queue_manager.delete_queue(queue.id)
                console.print("[green]✓ Queue deleted[/green]")
    
    input("\nPress Enter to continue...")


def handle_channel_search(downloader):
    """Handle searching channel for playlists"""
    console.print("\n[cyan]Search Channel for Playlists[/cyan]")
    
    channel_url = Prompt.ask("\nChannel URL")
    
    console.print("\n[yellow]Searching for playlists...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]")
    
    playlists = downloader.search_channel_playlists(channel_url)
    
    if not playlists:
        console.print("\n[yellow]No playlists found in this channel[/yellow]")
        console.print("\n[cyan]Tips:[/cyan]")
        console.print("  • Make sure the URL is a channel page")
        console.print("  • Some channels don't have public playlists")
        console.print("  • Try the channel's 'Playlists' tab URL")
        input("\nPress Enter to continue...")
        return
    
    # Display playlists
    from rich.table import Table
    
    table = Table(title=f"Found {len(playlists)} Playlists", show_header=True)
    table.add_column("#", style="cyan", width=6)
    table.add_column("Playlist", style="white")
    table.add_column("Videos", style="green")
    
    for idx, playlist in enumerate(playlists, 1):
        table.add_row(
            str(idx),
            playlist['title'][:60],
            str(playlist['playlist_count'])
        )
    
    console.print("\n")
    console.print(table)
    
    # Show playlist URLs
    console.print("\n[dim]Playlist URLs:[/dim]")
    for idx, playlist in enumerate(playlists, 1):
        console.print(f"[dim]{idx}. {playlist['url']}[/dim]")
    
    console.print("\n[cyan]Copy the URL of the playlist you want to download[/cyan]")
    console.print("[cyan]Then use 'Download new playlist' from the main menu[/cyan]")
    
    input("\nPress Enter to continue...")


def handle_view_queue(queue_manager):
    """Handle viewing queue status"""
    console.print("\n[cyan]Queue Status[/cyan]")
    
    all_queues = queue_manager.get_all_queues()
    
    if not all_queues:
        console.print("\n[yellow]No queues found[/yellow]")
        console.print("\nUse 'Download new playlist' to create a queue.")
        input("\nPress Enter to continue...")
        return
    
    from rich.table import Table
    
    table = Table(title=f"All Queues ({len(all_queues)})", show_header=True)
    table.add_column("#", style="cyan", width=6)
    table.add_column("Playlist", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Progress", style="green")
    table.add_column("Format", style="magenta")
    table.add_column("Storage", style="blue")
    table.add_column("Created", style="white")
    
    for idx, queue in enumerate(all_queues, 1):
        items = queue_manager.get_queue_items(queue.id)
        
        from enums import DownloadStatus
        completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
        failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
        total = len(items)
        
        if queue.completed_at:
            status = "✓ Completed"
            status_style = "green"
        elif completed == 0:
            status = "Pending"
            status_style = "yellow"
        elif completed < total:
            status = "In Progress"
            status_style = "cyan"
        else:
            status = "✓ Completed"
            status_style = "green"
        
        progress = f"{completed}/{total}"
        if failed > 0:
            progress += f" ({failed} failed)"
        
        created_date = queue.created_at[:10] if queue.created_at else "Unknown"
        
        table.add_row(
            str(idx),
            queue.playlist_title[:40],
            f"[{status_style}]{status}[/{status_style}]",
            progress,
            queue.format_type,
            queue.storage_provider,
            created_date
        )
    
    console.print("\n")
    console.print(table)
    
    # Show summary statistics
    total_items = sum(len(queue_manager.get_queue_items(q.id)) for q in all_queues)
    
    from enums import DownloadStatus
    all_items = []
    for queue in all_queues:
        all_items.extend(queue_manager.get_queue_items(queue.id))
    
    total_completed = sum(1 for item in all_items if item.status == DownloadStatus.COMPLETED.value)
    total_failed = sum(1 for item in all_items if item.status == DownloadStatus.FAILED.value)
    total_pending = sum(1 for item in all_items if item.status == DownloadStatus.PENDING.value)
    
    # Calculate total size
    total_size_bytes = sum(
        item.file_size_bytes or 0 
        for item in all_items 
        if item.status == DownloadStatus.COMPLETED.value
    )
    total_size_mb = total_size_bytes / (1024 * 1024)
    total_size_gb = total_size_mb / 1024
    
    if total_size_gb >= 1:
        size_str = f"{total_size_gb:.2f} GB"
    else:
        size_str = f"{total_size_mb:.1f} MB"
    
    summary_panel = Panel(
        f"[cyan]Total Queues:[/cyan] {len(all_queues)}\n"
        f"[cyan]Total Items:[/cyan] {total_items}\n\n"
        f"[green]Completed:[/green] {total_completed}\n"
        f"[yellow]Pending:[/yellow] {total_pending}\n"
        f"[red]Failed:[/red] {total_failed}\n\n"
        f"[cyan]Total Downloaded:[/cyan] {size_str}",
        title="[bold]Summary[/bold]",
        border_style="cyan"
    )
    
    console.print("\n")
    console.print(summary_panel)
    
    # Options
    console.print("\n[cyan]Options:[/cyan]")
    console.print("  1. View queue details")
    console.print("  2. Delete queue")
    console.print("  3. Back to main menu")
    
    option = Prompt.ask("Select option", choices=["1", "2", "3"], default="3")

    if option == "1":
        selection = IntPrompt.ask(
            "\nQueue number to view (0 to cancel)",
            default=0
        )
        
        if selection > 0 and selection <= len(all_queues):
            queue = all_queues[selection - 1]
            _display_queue_details(queue, queue_manager)
    
    elif option == "2":
        selection = IntPrompt.ask(
            "\nQueue number to delete (0 to cancel)",
            default=0
        )
        
        if selection > 0 and selection <= len(all_queues):
            queue = all_queues[selection - 1]
            
            if Confirm.ask(f"\nDelete queue '{queue.playlist_title}'?", default=False):
                queue_manager.delete_queue(queue.id)
                console.print("[green]✓ Queue deleted[/green]")
                input("\nPress Enter to continue...")


def _display_queue_details(queue, queue_manager):
    """Display detailed information about a queue"""
    from rich.table import Table
    
    console.print("\n")
    
    # Queue info
    info_panel = Panel(
        f"[bold cyan]Playlist:[/bold cyan] {queue.playlist_title}\n"
        f"[cyan]URL:[/cyan] {queue.playlist_url}\n"
        f"[cyan]Format:[/cyan] {queue.format_type}\n"
        f"[cyan]Quality:[/cyan] {queue.quality}\n"
        f"[cyan]Output:[/cyan] {queue.output_dir}\n"
        f"[cyan]Storage:[/cyan] {queue.storage_provider}\n"
        f"[cyan]Order:[/cyan] {queue.download_order}\n"
        f"[cyan]Template:[/cyan] {queue.filename_template or 'None'}\n"
        f"[cyan]Created:[/cyan] {queue.created_at}\n"
        f"[cyan]Completed:[/cyan] {queue.completed_at or 'In progress'}",
        title="[bold]Queue Details[/bold]",
        border_style="cyan"
    )
    console.print(info_panel)
    
    # Items
    items = queue_manager.get_queue_items(queue.id)
    
    from enums import DownloadStatus
    
    # Categorize items
    completed_items = [item for item in items if item.status == DownloadStatus.COMPLETED.value]
    failed_items = [item for item in items if item.status == DownloadStatus.FAILED.value]
    pending_items = [item for item in items if item.status == DownloadStatus.PENDING.value]
    
    console.print(f"\n[cyan]Items ({len(items)} total):[/cyan]")
    
    # Show completed items (limited)
    if completed_items:
        console.print(f"\n[green]Completed ({len(completed_items)}):[/green]")
        for item in completed_items[:5]:
            size_str = ""
            if item.file_size_bytes:
                size_mb = item.file_size_bytes / (1024 * 1024)
                size_str = f" ({size_mb:.1f} MB)"
            console.print(f"  ✓ {item.title[:60]}{size_str}")
        
        if len(completed_items) > 5:
            console.print(f"  [dim]... and {len(completed_items) - 5} more[/dim]")
    
    # Show failed items
    if failed_items:
        console.print(f"\n[red]Failed ({len(failed_items)}):[/red]")
        for item in failed_items[:5]:
            error_msg = item.error[:50] if item.error else "Unknown error"
            console.print(f"  ✗ {item.title[:50]}: {error_msg}")
        
        if len(failed_items) > 5:
            console.print(f"  [dim]... and {len(failed_items) - 5} more[/dim]")
    
    # Show pending items
    if pending_items:
        console.print(f"\n[yellow]Pending ({len(pending_items)}):[/yellow]")
        for item in pending_items[:5]:
            console.print(f"  • {item.title[:60]}")
        
        if len(pending_items) > 5:
            console.print(f"  [dim]... and {len(pending_items) - 5} more[/dim]")
    
    input("\nPress Enter to continue...")


def handle_view_stats(stats_manager):
    """Handle viewing download statistics"""
    from rich.table import Table
    
    console.print("\n[cyan]Download Statistics[/cyan]")
    
    if not stats_manager:
        console.print("\n[yellow]Statistics not available[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    # Get statistics
    today_stats = stats_manager.get_today_stats()
    all_time_stats = stats_manager.get_all_time_stats()
    
    # Summary panel
    today_size_mb = today_stats.total_file_size_bytes / (1024 * 1024)
    all_time_size_gb = all_time_stats.total_file_size_bytes / (1024 * 1024 * 1024)
    
    today_success_rate = (
        (today_stats.successful_downloads / today_stats.total_downloads * 100)
        if today_stats.total_downloads > 0 else 0
    )
    
    all_time_success_rate = (
        (all_time_stats.successful_downloads / all_time_stats.total_downloads * 100)
        if all_time_stats.total_downloads > 0 else 0
    )
    
    summary_panel = Panel(
        f"[bold cyan]Today:[/bold cyan]\n"
        f"  Downloads: {today_stats.total_downloads}\n"
        f"  Successful: {today_stats.successful_downloads}\n"
        f"  Failed: {today_stats.failed_downloads}\n"
        f"  Success Rate: {today_success_rate:.1f}%\n"
        f"  Data: {today_size_mb:.1f} MB\n"
        f"  Queues: {today_stats.queues_completed}\n\n"
        f"[bold cyan]All Time:[/bold cyan]\n"
        f"  Downloads: {all_time_stats.total_downloads}\n"
        f"  Successful: {all_time_stats.successful_downloads}\n"
        f"  Failed: {all_time_stats.failed_downloads}\n"
        f"  Success Rate: {all_time_success_rate:.1f}%\n"
        f"  Data: {all_time_size_gb:.2f} GB\n"
        f"  Queues: {all_time_stats.queues_completed}",
        title="[bold]Statistics Summary[/bold]",
        border_style="cyan"
    )
    
    console.print("\n")
    console.print(summary_panel)
    
    # Download history (last 7 days)
    console.print("\n[cyan]Last 7 Days:[/cyan]")
    
    history_table = Table(show_header=True)
    history_table.add_column("Date", style="cyan")
    history_table.add_column("Downloads", style="green")
    history_table.add_column("Success", style="white")
    history_table.add_column("Failed", style="red")
    history_table.add_column("Data", style="yellow")
    
    from datetime import datetime, timedelta
    
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        day_stats = stats_manager.get_stats_for_date(date_str)
        
        if day_stats.total_downloads > 0:
            size_mb = day_stats.total_file_size_bytes / (1024 * 1024)
            history_table.add_row(
                date_str,
                str(day_stats.total_downloads),
                str(day_stats.successful_downloads),
                str(day_stats.failed_downloads),
                f"{size_mb:.1f} MB"
            )
    
    console.print("\n")
    console.print(history_table)
    
    # Alert thresholds status
    console.print("\n[cyan]Alert Thresholds:[/cyan]")
    
    for threshold_mb in [250, 1000, 5000, 10000]:
        threshold_bytes = threshold_mb * 1024 * 1024
        if today_stats.total_file_size_bytes >= threshold_bytes:
            console.print(f"  [green]✓[/green] {threshold_mb} MB threshold reached")
        else:
            remaining_mb = (threshold_bytes - today_stats.total_file_size_bytes) / (1024 * 1024)
            console.print(f"  [dim]• {threshold_mb} MB ({remaining_mb:.1f} MB remaining)[/dim]")
    
    input("\nPress Enter to continue...")


def handle_monitoring(monitor_manager, downloader, queue_manager, config_manager, slack_notifier):
    """Handle monitoring submenu"""
    while True:
        choice = MonitoringMenu.display_monitoring_menu(
            monitor_manager, downloader, queue_manager, 
            config_manager, slack_notifier
        )
        
        if choice == "1":
            MonitoringMenu.add_channel_to_monitoring(
                monitor_manager, downloader, config_manager
            )
        elif choice == "2":
            MonitoringMenu.remove_channel_from_monitoring(monitor_manager)
        elif choice == "3":
            if not monitor_manager.is_running:
                monitor_manager.start_monitoring(
                    downloader, queue_manager, config_manager, slack_notifier
                )
                console.print("\n[green]✓ Monitoring started[/green]")
            else:
                console.print("\n[yellow]Monitoring is already running[/yellow]")
            input("\nPress Enter to continue...")
        elif choice == "4":
            if monitor_manager.is_running:
                monitor_manager.stop_monitoring()
                console.print("\n[yellow]Monitoring stopped[/yellow]")
            else:
                console.print("\n[yellow]Monitoring is not running[/yellow]")
            input("\nPress Enter to continue...")
        elif choice == "5":
            console.print("\n[cyan]Checking all monitored channels...[/cyan]")
            monitor_manager.check_all_channels(
                downloader, queue_manager, config_manager, slack_notifier
            )
            console.print("\n[green]✓ Check completed[/green]")
            input("\nPress Enter to continue...")
        elif choice == "6":
            break


def handle_proxy_management(proxy_manager, config_manager):
    """Handle proxy management submenu"""
    console.print("\n[cyan]Proxy Management[/cyan]")
    
    if proxy_manager.proxies:
        console.print(f"\n[green]Current proxies: {len(proxy_manager.proxies)}[/green]")
        proxy_manager.display_proxy_list(max_display=15)
    else:
        console.print("\n[yellow]No proxies configured[/yellow]")
        console.print("\nTo use proxies, create one of these files:")
        console.print("  • proxies.txt (one proxy per line: http://ip:port)")
        console.print("  • proxies.csv (format: ip,port,country,https,...)\n")
    
    options = [
        ("1", "Reload proxies from file"),
        ("2", "Validate all proxies"),
        ("3", "Remove non-working proxies"),
        ("4", "Show all proxies"),
        ("5", "Back")
    ]
    
    option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
    console.print(f"\n{option_text}\n")
    
    choice = Prompt.ask("Select option", choices=[num for num, _ in options], default="5")
    
    if choice == "1":
        if proxy_manager.load_proxies_from_file():
            config_manager.config.proxies = proxy_manager.proxies
            config_manager.save_config()
        input("\nPress Enter to continue...")
    
    elif choice == "2":
        if not proxy_manager.proxies:
            console.print("\n[yellow]No proxies to validate. Load proxies first.[/yellow]")
        else:
            timeout = IntPrompt.ask("Proxy timeout (seconds)", default=10)
            workers = IntPrompt.ask("Concurrent validation workers", default=5)
            auto_remove = Confirm.ask("Automatically remove failed proxies?", default=True)
            
            proxy_manager.validate_all_proxies(timeout, workers, auto_remove)
            
            # Update config
            config_manager.config.proxies = proxy_manager.proxies
            config_manager.save_config()
        
        input("\nPress Enter to continue...")
    
    elif choice == "3":
        if not proxy_manager.working_proxies:
            console.print("\n[yellow]Run validation first (option 2)[/yellow]")
        else:
            proxy_manager.remove_dead_proxies()
            config_manager.config.proxies = proxy_manager.proxies
            config_manager.save_config()
        
        input("\nPress Enter to continue...")
    
    elif choice == "4":
        proxy_manager.display_proxy_list(max_display=100)
        input("\nPress Enter to continue...")
    
    elif choice == "5":
        pass  # Return to settings menu

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
