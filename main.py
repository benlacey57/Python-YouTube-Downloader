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


# Other handler functions remain the same...
# (handle_resume_download, handle_channel_search, handle_view_queue, 
#  handle_view_stats, handle_monitoring, handle_proxy_management)


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
