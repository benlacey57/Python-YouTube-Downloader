"""Initial setup wizard"""
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class SetupWizard:
    """Guides user through initial setup"""
    
    @staticmethod
    def run(config_manager):
        """Run the setup wizard"""
        console.clear()
        
        welcome_panel = Panel(
            "[bold cyan]Welcome to Playlist Downloader Pro![/bold cyan]\n\n"
            "This wizard will help you configure the application.\n"
            "You can change these settings later in the Settings menu.",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(welcome_panel)
        
        if not Confirm.ask("\nWould you like to run the setup wizard?", default=True):
            config_manager.config.setup_completed = True
            config_manager.save_config()
            return
        
        # Step 1: Authentication
        SetupWizard._setup_authentication(config_manager)
        
        # Step 2: Default Quality
        SetupWizard._setup_quality(config_manager)
        
        # Step 3: Parallel Downloads
        SetupWizard._setup_workers(config_manager)
        
        # Step 4: Rate Limiting
        SetupWizard._setup_rate_limiting(config_manager)
        
        # Step 5: Storage
        SetupWizard._setup_storage(config_manager)
        
        # Step 6: Notifications (optional)
        SetupWizard._setup_notifications(config_manager)
        
        # Mark setup as completed
        config_manager.config.setup_completed = True
        config_manager.save_config()
        
        # Show summary
        SetupWizard._show_summary(config_manager)
        
        console.print("\n[green]✓ Setup completed successfully![/green]")
        console.print("[cyan]You can now start downloading playlists.[/cyan]")
        input("\nPress Enter to continue...")
    
    @staticmethod
    def _setup_authentication(config_manager):
        """Setup authentication"""
        console.print("\n[bold cyan]Step 1: Authentication[/bold cyan]")
        console.print("\nFor age-restricted or private content, you need authentication.")
        
        if Confirm.ask("Configure authentication now?", default=True):
            console.print("\n[yellow]To export cookies:[/yellow]")
            console.print("1. Install 'Get cookies.txt LOCALLY' browser extension")
            console.print("2. Visit YouTube whilst logged in")
            console.print("3. Export cookies to a file")
            
            cookies_file = Prompt.ask("\nCookies file path (leave blank to skip)", default="")
            
            if cookies_file:
                from pathlib import Path
                if Path(cookies_file).exists():
                    config_manager.config.cookies_file = cookies_file
                    console.print("[green]✓ Authentication configured[/green]")
                else:
                    console.print("[yellow]File not found, skipping authentication[/yellow]")
            else:
                console.print("[yellow]Skipping authentication[/yellow]")
        
        config_manager.save_config()
    
    @staticmethod
    def _setup_quality(config_manager):
        """Setup default quality"""
        console.print("\n[bold cyan]Step 2: Default Quality Settings[/bold cyan]")
        
        # Video quality
        console.print("\n[cyan]Video Quality:[/cyan]")
        console.print("  1. Best available")
        console.print("  2. 1080p (Full HD)")
        console.print("  3. 720p (HD) - Recommended")
        console.print("  4. 480p (SD)")
        console.print("  5. 360p (Low)")
        
        video_choice = Prompt.ask(
            "Select default video quality",
            choices=["1", "2", "3", "4", "5"],
            default="3"
        )
        
        video_qualities = ["best", "1080p", "720p", "480p", "360p"]
        config_manager.config.default_video_quality = video_qualities[int(video_choice) - 1]
        
        # Audio quality
        console.print("\n[cyan]Audio Quality:[/cyan]")
        console.print("  1. 320kbps (High)")
        console.print("  2. 192kbps (Standard) - Recommended")
        console.print("  3. 128kbps (Low)")
        
        audio_choice = Prompt.ask(
            "Select default audio quality",
            choices=["1", "2", "3"],
            default="2"
        )
        
        audio_qualities = ["320", "192", "128"]
        config_manager.config.default_audio_quality = audio_qualities[int(audio_choice) - 1]
        
        console.print(f"\n[green]✓ Quality set to {config_manager.config.default_video_quality} / {config_manager.config.default_audio_quality}kbps[/green]")
        config_manager.save_config()
    
    @staticmethod
    def _setup_workers(config_manager):
        """Setup parallel downloads"""
        console.print("\n[bold cyan]Step 3: Parallel Downloads[/bold cyan]")
        console.print("\nHow many videos should download simultaneously?")
        console.print("  • 1-2: Slow connection")
        console.print("  • 3-4: Balanced (Recommended)")
        console.print("  • 5+: Fast connection")
        
        workers = IntPrompt.ask(
            "\nNumber of parallel downloads",
            default=3
        )
        
        config_manager.config.max_workers = max(1, min(10, workers))
        console.print(f"[green]✓ Set to {config_manager.config.max_workers} parallel downloads[/green]")
        config_manager.save_config()
    
    @staticmethod
    def _setup_rate_limiting(config_manager):
        """Setup rate limiting"""
        console.print("\n[bold cyan]Step 4: Rate Limiting[/bold cyan]")
        console.print("\nRate limiting helps avoid IP bans and rate limits.")
        console.print("\nPresets:")
        console.print("  1. Conservative (30/hour, 3-7s delay)")
        console.print("  2. Moderate (50/hour, 2-5s delay) - Recommended")
        console.print("  3. Aggressive (100/hour, 1-3s delay)")
        console.print("  4. Custom")
        
        choice = Prompt.ask(
            "Select preset",
            choices=["1", "2", "3", "4"],
            default="2"
        )
        
        if choice == "1":
            config_manager.config.max_downloads_per_hour = 30
            config_manager.config.min_delay_seconds = 3.0
            config_manager.config.max_delay_seconds = 7.0
        elif choice == "2":
            config_manager.config.max_downloads_per_hour = 50
            config_manager.config.min_delay_seconds = 2.0
            config_manager.config.max_delay_seconds = 5.0
        elif choice == "3":
            config_manager.config.max_downloads_per_hour = 100
            config_manager.config.min_delay_seconds = 1.0
            config_manager.config.max_delay_seconds = 3.0
        else:
            max_per_hour = IntPrompt.ask("Max downloads per hour", default=50)
            min_delay = float(Prompt.ask("Min delay (seconds)", default="2"))
            max_delay = float(Prompt.ask("Max delay (seconds)", default="5"))
            
            config_manager.config.max_downloads_per_hour = max_per_hour
            config_manager.config.min_delay_seconds = min_delay
            config_manager.config.max_delay_seconds = max_delay
        
        console.print(f"[green]✓ Rate limiting configured[/green]")
        config_manager.save_config()
    
    @staticmethod
    def _setup_storage(config_manager):
        """Setup storage"""
        console.print("\n[bold cyan]Step 5: Storage Configuration[/bold cyan]")
        console.print("\nWhere should downloads be stored?")
        console.print("  1. Local storage only (default)")
        console.print("  2. Configure remote storage (FTP/SFTP/Cloud)")
        
        choice = Prompt.ask("Select option", choices=["1", "2"], default="1")
        
        if choice == "2":
            console.print("\n[cyan]Remote storage types:[/cyan]")
            console.print("  1. FTP")
            console.print("  2. SFTP")
            console.print("  3. Google Drive")
            console.print("  4. Dropbox")
            console.print("  5. OneDrive")
            console.print("  6. Skip for now")
            
            storage_choice = Prompt.ask(
                "Select storage type",
                choices=["1", "2", "3", "4", "5", "6"],
                default="6"
            )
            
            if storage_choice != "6":
                from ui.storage_menu import StorageMenu
                
                if storage_choice == "1":
                    StorageMenu.add_ftp_storage(config_manager)
                elif storage_choice == "2":
                    StorageMenu.add_sftp_storage(config_manager)
                elif storage_choice == "3":
                    StorageMenu.add_google_drive_storage(config_manager)
                elif storage_choice == "4":
                    StorageMenu.add_dropbox_storage(config_manager)
                elif storage_choice == "5":
                    StorageMenu.add_onedrive_storage(config_manager)
        else:
            console.print("[green]✓ Using local storage[/green]")
    
    @staticmethod
    def _setup_notifications(config_manager):
        """Setup notifications"""
        console.print("\n[bold cyan]Step 6: Notifications (Optional)[/bold cyan]")
        
        if Confirm.ask("Configure Slack notifications?", default=False):
            console.print("\nTo get a webhook URL:")
            console.print("  1. Go to https://api.slack.com/apps")
            console.print("  2. Create app and enable 'Incoming Webhooks'")
            console.print("  3. Copy the webhook URL")
            
            webhook = Prompt.ask("\nSlack webhook URL (or leave blank to skip)", default="")
            
            if webhook:
                config_manager.config.slack_webhook_url = webhook
                console.print("[green]✓ Slack notifications configured[/green]")
        
        config_manager.save_config()
    
    @staticmethod
    def _show_summary(config_manager):
        """Show configuration summary"""
        from rich.table import Table
        
        console.print("\n")
        
        summary_panel = Panel(
            "[bold]Setup Complete![/bold]\n\n"
            "Here's your configuration:",
            border_style="green"
        )
        console.print(summary_panel)
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Authentication", "Configured" if config_manager.config.cookies_file else "Not configured")
        table.add_row("Video Quality", config_manager.config.default_video_quality)
        table.add_row("Audio Quality", f"{config_manager.config.default_audio_quality}kbps")
        table.add_row("Parallel Downloads", str(config_manager.config.max_workers))
        table.add_row("Rate Limit", f"{config_manager.config.max_downloads_per_hour}/hour")
        table.add_row("Storage Providers", str(len(config_manager.config.storage_providers)))
        table.add_row("Slack Notifications", "Enabled" if config_manager.config.slack_webhook_url else "Disabled")
        
        console.print("\n")
        console.print(table)


class StatusPage:
    """Display system status and connection information"""
    
    @staticmethod
    def display(config_manager, storage_manager, proxy_manager, stats_manager):
        """Display comprehensive status page"""
        from rich.table import Table
        from rich.layout import Layout
        from rich.panel import Panel
        
        console.clear()
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Header
        header = Panel(
            "[bold cyan]System Status Dashboard[/bold cyan]",
            border_style="cyan"
        )
        layout["header"].update(header)
        
        # Left panel - Configuration Status
        config_table = Table(title="Configuration", show_header=True, box=None)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        
        config_table.add_row("Setup Completed", "✓ Yes" if config_manager.config.setup_completed else "✗ No")
        config_table.add_row("Authentication", "✓ Configured" if config_manager.config.cookies_file else "✗ Not configured")
        config_table.add_row("Default Storage", config_manager.config.default_storage)
        config_table.add_row("Video Quality", config_manager.config.default_video_quality)
        config_table.add_row("Audio Quality", f"{config_manager.config.default_audio_quality}kbps")
        config_table.add_row("Parallel Downloads", str(config_manager.config.max_workers))
        config_table.add_row("Rate Limit", f"{config_manager.config.max_downloads_per_hour}/hour")
        config_table.add_row("Bandwidth Limit", 
                            f"{config_manager.config.bandwidth_limit_mbps} Mbps" 
                            if config_manager.config.bandwidth_limit_mbps 
                            else "Unlimited")
        config_table.add_row("Filename Normalization", "✓ Enabled" if config_manager.config.normalize_filenames else "✗ Disabled")
        
        # Storage status
        storage_table = Table(title="Storage Providers", show_header=True, box=None)
        storage_table.add_column("Name", style="cyan")
        storage_table.add_column("Type", style="yellow")
        storage_table.add_column("Status", style="white")
        storage_table.add_column("Connection", style="green")
        
        if config_manager.config.storage_providers:
            from utils.storage_providers import (
                FTPStorage, SFTPStorage, GoogleDriveStorage,
                DropboxStorage, OneDriveStorage
            )
            
            for name, config_dict in config_manager.config.storage_providers.items():
                from managers.config_manager import StorageConfig
                storage_config = StorageConfig.from_dict(config_dict)
                
                status = "✓ Enabled" if storage_config.enabled else "✗ Disabled"
                
                # Test connection
                connection_status = "Unknown"
                if storage_config.enabled:
                    try:
                        provider = None
                        
                        if storage_config.provider_type == "ftp":
                            provider = FTPStorage(
                                storage_config.host,
                                storage_config.port,
                                storage_config.username,
                                storage_config.password,
                                storage_config.base_path
                            )
                        elif storage_config.provider_type == "sftp":
                            provider = SFTPStorage(
                                storage_config.host,
                                storage_config.port,
                                storage_config.username,
                                storage_config.password,
                                storage_config.key_filename,
                                storage_config.base_path
                            )
                        elif storage_config.provider_type == "gdrive":
                            provider = GoogleDriveStorage(
                                storage_config.credentials_file,
                                storage_config.folder_id
                            )
                        elif storage_config.provider_type == "dropbox":
                            provider = DropboxStorage(
                                storage_config.access_token,
                                storage_config.base_path
                            )
                        elif storage_config.provider_type == "onedrive":
                            provider = OneDriveStorage(
                                storage_config.client_id,
                                storage_config.client_secret,
                                storage_config.base_path
                            )
                        
                        if provider and provider.connect():
                            connection_status = "✓ Connected"
                            provider.disconnect()
                        else:
                            connection_status = "✗ Failed"
                    except:
                        connection_status = "✗ Error"
                
                storage_table.add_row(
                    name,
                    storage_config.provider_type.upper(),
                    status,
                    connection_status
                )
        else:
            storage_table.add_row("Local", "LOCAL", "✓ Enabled", "✓ Available")
        
        # Proxy status
        proxy_table = Table(title="Proxy Status", show_header=True, box=None)
        proxy_table.add_column("Metric", style="cyan")
        proxy_table.add_column("Value", style="white")
        
        if proxy_manager and proxy_manager.proxies:
            summary = proxy_manager.get_summary()
            proxy_table.add_row("Total Proxies", str(summary['total_proxies']))
            proxy_table.add_row("Working Proxies", str(summary['working_proxies']))
            proxy_table.add_row("Failed Proxies", str(summary['failed_proxies']))
            proxy_table.add_row("Success Rate", f"{summary['success_rate']:.1f}%")
        else:
            proxy_table.add_row("Status", "No proxies configured")
        
        # Statistics
        stats_table = Table(title="Download Statistics", show_header=True, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Today", style="green")
        stats_table.add_column("Total", style="blue")
        
        if stats_manager:
            today_stats = stats_manager.get_today_stats()
            all_time_stats = stats_manager.get_all_time_stats()
            
            stats_table.add_row(
                "Downloads",
                str(today_stats.total_downloads),
                str(all_time_stats.total_downloads)
            )
            stats_table.add_row(
                "Successful",
                str(today_stats.successful_downloads),
                str(all_time_stats.successful_downloads)
            )
            stats_table.add_row(
                "Failed",
                str(today_stats.failed_downloads),
                str(all_time_stats.failed_downloads)
            )
            
            today_size_mb = today_stats.total_file_size_bytes / (1024 * 1024)
            all_time_size_mb = all_time_stats.total_file_size_bytes / (1024 * 1024)
            
            stats_table.add_row(
                "Data Downloaded",
                f"{today_size_mb:.1f} MB",
                f"{all_time_size_mb:.1f} MB"
            )
            stats_table.add_row(
                "Queues Completed",
                str(today_stats.queues_completed),
                str(all_time_stats.queues_completed)
            )
        else:
            stats_table.add_row("Status", "Not available", "")
        
        # Combine left panels
        left_content = Table.grid(padding=1)
        left_content.add_row(config_table)
        left_content.add_row(proxy_table)
        
        # Combine right panels
        right_content = Table.grid(padding=1)
        right_content.add_row(storage_table)
        right_content.add_row(stats_table)
        
        layout["left"].update(Panel(left_content, border_style="blue"))
        layout["right"].update(Panel(right_content, border_style="green"))
        
        console.print(layout)
        console.print("\n[dim]Press any key to return to menu...[/dim]")
        input()
