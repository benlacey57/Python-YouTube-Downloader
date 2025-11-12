"""Setup wizard for first-time configuration"""
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

from managers.config_manager import ConfigManager

console = Console()


class SetupWizard:
    """Interactive setup wizard"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def run(self) -> bool:
        """Run the setup wizard"""
        console.clear()
        
        header = Panel(
            "[bold cyan]Setup Wizard[/bold cyan]\n"
            "Quick configuration for YouTube Playlist Downloader",
            border_style="cyan"
        )
        console.print(header)
        
        # Show default configuration summary
        self._show_defaults_summary()
        
        console.print("\n[yellow]The application is ready to use with these defaults.[/yellow]")
        
        # Ask if user wants to customize
        if not Confirm.ask("\nWould you like to customize these settings?", default=False):
            # Mark setup as completed and return to main menu
            self.config_manager.config.setup_completed = True
            self.config_manager.save_config()
            console.print("\n[green]✓ Setup completed with default settings[/green]")
            input("\nPress Enter to continue...")
            return True
        
        # Show configuration sections menu
        while True:
            choice = self._show_sections_menu()
            
            if choice == "1":
                self._configure_download_settings()
            elif choice == "2":
                self._configure_notifications()
            elif choice == "3":
                self._configure_rate_limiting()
            elif choice == "4":
                self._configure_quality_settings()
            elif choice == "5":
                self._configure_storage()
            elif choice == "6":
                # Show updated summary
                console.clear()
                console.print(Panel("[bold cyan]Updated Configuration Summary[/bold cyan]", border_style="cyan"))
                self._show_defaults_summary()
                input("\nPress Enter to continue...")
            elif choice == "7":
                # Finish setup
                break
        
        # Mark setup as completed
        self.config_manager.config.setup_completed = True
        self.config_manager.save_config()
        
        console.print("\n[bold green]✓ Setup completed![/bold green]")
        console.print("[dim]You can change these settings anytime from the Settings menu.[/dim]")
        
        input("\nPress Enter to continue...")
        return True
    
    def _show_defaults_summary(self):
        """Show summary of default configuration"""
        config = self.config_manager.config
        
        # Download Settings Table
        download_table = Table(title="Download Settings", show_header=True, title_style="bold cyan")
        download_table.add_column("Setting", style="cyan", width=30)
        download_table.add_column("Value", style="green")
        
        download_table.add_row("Default Video Quality", config.default_video_quality)
        download_table.add_row("Default Audio Quality", f"{config.default_audio_quality} kbps")
        download_table.add_row("Parallel Downloads", str(config.max_workers))
        download_table.add_row("Download Timeout", f"{config.download_timeout_seconds}s")
        download_table.add_row("Filename Normalization", "✓ Enabled" if config.normalize_filenames else "✗ Disabled")
        
        console.print("\n")
        console.print(download_table)
        
        # Notifications Table
        notif_table = Table(title="Notifications", show_header=True, title_style="bold cyan")
        notif_table.add_column("Setting", style="cyan", width=30)
        notif_table.add_column("Value", style="green")
        
        notif_table.add_row("Notifications Enabled", "✓ Yes" if config.notifications_enabled else "✗ No")
        notif_table.add_row("Slack", "✓ Configured" if config.slack_enabled else "✗ Not configured")
        notif_table.add_row("Email", "✓ Configured" if config.email_enabled else "✗ Not configured")
        notif_table.add_row("Daily Summary", "✓ Enabled" if config.send_daily_summary else "✗ Disabled")
        notif_table.add_row("Weekly Stats", "✓ Enabled" if config.send_weekly_stats else "✗ Disabled")
        
        console.print("\n")
        console.print(notif_table)
        
        # Rate Limiting Table
        rate_table = Table(title="Rate Limiting", show_header=True, title_style="bold cyan")
        rate_table.add_column("Setting", style="cyan", width=30)
        rate_table.add_column("Value", style="green")
        
        rate_table.add_row("Max Downloads per Hour", str(config.max_downloads_per_hour))
        rate_table.add_row("Min Delay", f"{config.min_delay_seconds}s")
        rate_table.add_row("Max Delay", f"{config.max_delay_seconds}s")
        
        if config.bandwidth_limit_mbps:
            rate_table.add_row("Bandwidth Limit", f"{config.bandwidth_limit_mbps} Mbps")
        else:
            rate_table.add_row("Bandwidth Limit", "Unlimited")
        
        console.print("\n")
        console.print(rate_table)
        
        # Storage Table
        storage_table = Table(title="Storage", show_header=True, title_style="bold cyan")
        storage_table.add_column("Setting", style="cyan", width=30)
        storage_table.add_column("Value", style="green")
        
        storage_table.add_row("Default Storage", config.default_storage.upper())
        storage_table.add_row("Storage Providers", str(len(config.storage_providers)))
        
        console.print("\n")
        console.print(storage_table)
    
    def _show_sections_menu(self) -> str:
        """Show configuration sections menu"""
        console.clear()
        
        header = Panel(
            "[bold cyan]Configuration Sections[/bold cyan]\n"
            "Select a section to configure",
            border_style="cyan"
        )
        console.print(header)
        
        console.print("\n[cyan]Available Sections:[/cyan]")
        console.print("  1. Download Settings")
        console.print("  2. Notifications")
        console.print("  3. Rate Limiting")
        console.print("  4. Quality Settings")
        console.print("  5. Storage Providers")
        console.print("  6. View Current Configuration")
        console.print("  7. Finish Setup")
        
        return Prompt.ask(
            "\nSelect section",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="7"
        )
    
    def _configure_download_settings(self):
        """Configure download settings"""
        console.clear()
        console.print(Panel("[bold cyan]Download Settings[/bold cyan]", border_style="cyan"))
        
        console.print("\n[yellow]Current Settings:[/yellow]")
        console.print(f"  Max Workers: {self.config_manager.config.max_workers}")
        console.print(f"  Timeout: {self.config_manager.config.download_timeout_seconds}s")
        console.print(f"  Filename Normalization: {self.config_manager.config.normalize_filenames}")
        
        if not Confirm.ask("\nChange download settings?", default=False):
            return
        
        self.config_manager.config.max_workers = IntPrompt.ask(
            "\nMaximum parallel downloads",
            default=self.config_manager.config.max_workers
        )
        
        self.config_manager.config.download_timeout_seconds = IntPrompt.ask(
            "Download timeout (seconds)",
            default=self.config_manager.config.download_timeout_seconds
        )
        
        self.config_manager.config.normalize_filenames = Confirm.ask(
            "Normalize filenames? (removes special characters)",
            default=self.config_manager.config.normalize_filenames
        )
        
        self.config_manager.save_config()
        console.print("\n[green]✓ Download settings updated[/green]")
        input("\nPress Enter to continue...")
    
    def _configure_notifications(self):
        """Configure notifications"""
        console.clear()
        console.print(Panel("[bold cyan]Notifications[/bold cyan]", border_style="cyan"))
        
        console.print("\n[yellow]Current Settings:[/yellow]")
        console.print(f"  Enabled: {self.config_manager.config.notifications_enabled}")
        console.print(f"  Slack: {self.config_manager.config.slack_enabled}")
        console.print(f"  Email: {self.config_manager.config.email_enabled}")
        
        if not Confirm.ask("\nConfigure notifications?", default=False):
            return
        
        # Enable notifications
        self.config_manager.config.notifications_enabled = Confirm.ask(
            "\nEnable notifications?",
            default=self.config_manager.config.notifications_enabled
        )
        
        if not self.config_manager.config.notifications_enabled:
            self.config_manager.save_config()
            console.print("\n[yellow]Notifications disabled[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        # Choose providers
        console.print("\n[cyan]Which providers would you like to configure?[/cyan]")
        console.print("  1. Email (SMTP)")
        console.print("  2. Slack")
        console.print("  3. Both")
        console.print("  4. Skip")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"], default="4")
        
        if choice in ["1", "3"]:
            self._configure_email_provider()
        
        if choice in ["2", "3"]:
            self._configure_slack_provider()
        
        if choice != "4":
            # Configure what to notify about
            console.print("\n[cyan]Notification Preferences:[/cyan]")
            console.print("Choose which events should trigger notifications:\n")
            
            self.config_manager.config.notify_on_download_complete = Confirm.ask(
                "Notify on individual download complete?",
                default=self.config_manager.config.notify_on_download_complete
            )
            
            self.config_manager.config.notify_on_queue_complete = Confirm.ask(
                "Notify on queue complete?",
                default=self.config_manager.config.notify_on_queue_complete
            )
            
            self.config_manager.config.notify_on_error = Confirm.ask(
                "Notify on errors?",
                default=self.config_manager.config.notify_on_error
            )
            
            self.config_manager.config.notify_on_threshold = Confirm.ask(
                "Notify on size thresholds?",
                default=self.config_manager.config.notify_on_threshold
            )
        
        self.config_manager.save_config()
        console.print("\n[green]✓ Notifications configured[/green]")
        input("\nPress Enter to continue...")
    
    def _configure_email_provider(self):
        """Configure email notifications"""
        console.print("\n[bold yellow]Email (SMTP) Configuration[/bold yellow]")
        
        console.print("\n[dim]Common providers:[/dim]")
        console.print("  Gmail: smtp.gmail.com:587")
        console.print("  Outlook: smtp-mail.outlook.com:587")
        console.print("  Yahoo: smtp.mail.yahoo.com:587")
        
        self.config_manager.config.smtp_host = Prompt.ask(
            "\nSMTP Host",
            default=self.config_manager.config.smtp_host or ""
        )
        
        self.config_manager.config.smtp_port = IntPrompt.ask(
            "SMTP Port",
            default=self.config_manager.config.smtp_port
        )
        
        self.config_manager.config.smtp_username = Prompt.ask(
            "SMTP Username (email)",
            default=self.config_manager.config.smtp_username or ""
        )
        
        self.config_manager.config.smtp_password = Prompt.ask(
            "SMTP Password",
            password=True
        )
        
        self.config_manager.config.smtp_from_email = Prompt.ask(
            "From Email",
            default=self.config_manager.config.smtp_username
        )
        
        to_emails = Prompt.ask(
            "To Email(s) (comma-separated)",
            default=",".join(self.config_manager.config.smtp_to_emails) if self.config_manager.config.smtp_to_emails else ""
        )
        
        self.config_manager.config.smtp_to_emails = [
            email.strip() for email in to_emails.split(',')
        ]
        
        self.config_manager.config.smtp_use_tls = Confirm.ask(
            "Use TLS?",
            default=self.config_manager.config.smtp_use_tls
        )
        
        self.config_manager.config.email_enabled = True
        
        # Automated reports
        console.print("\n[yellow]Automated Email Reports:[/yellow]")
        self.config_manager.config.send_daily_summary = Confirm.ask(
            "Send daily summary email?",
            default=self.config_manager.config.send_daily_summary
        )
        
        self.config_manager.config.send_weekly_stats = Confirm.ask(
            "Send weekly statistics email?",
            default=self.config_manager.config.send_weekly_stats
        )
        
        if self.config_manager.config.send_daily_summary:
            self.config_manager.config.daily_summary_time = Prompt.ask(
                "Daily summary time (HH:MM)",
                default=self.config_manager.config.daily_summary_time
            )
        
        self.config_manager.save_config()
        console.print("[green]✓ Email notifications configured[/green]")
        
        # Test email
        if Confirm.ask("\nSend test email?", default=True):
            from managers.notification_manager import NotificationManager
            
            notification_manager = NotificationManager(self.config_manager.config)
            
            if notification_manager.email and notification_manager.email.is_configured():
                if notification_manager.email.send_notification(
                    "Test Email",
                    "This is a test email from YouTube Playlist Downloader"
                ):
                    console.print("[green]✓ Test email sent successfully[/green]")
                else:
                    console.print("[red]✗ Failed to send test email[/red]")

    def _configure_slack_provider(self):
        """Configure Slack notifications"""
        console.print("\n[bold yellow]Slack Configuration[/bold yellow]")
        
        console.print("\n[dim]To get a webhook URL:[/dim]")
        console.print("  1. Go to https://api.slack.com/apps")
        console.print("  2. Create a new app or select existing")
        console.print("  3. Enable Incoming Webhooks")
        console.print("  4. Add webhook to workspace")
        console.print("  5. Copy the webhook URL")
        
        webhook_url = Prompt.ask(
            "\nSlack Webhook URL",
            default=self.config_manager.config.slack_webhook_url or ""
        )
        
        if webhook_url:
            self.config_manager.config.slack_webhook_url = webhook_url
            self.config_manager.config.slack_enabled = True
            self.config_manager.save_config()
            
            console.print("[green]✓ Slack notifications configured[/green]")
            
            # Test Slack
            if Confirm.ask("\nSend test notification?", default=True):
                from managers.notification_manager import NotificationManager
                
                notification_manager = NotificationManager(self.config_manager.config)
                
                if notification_manager.slack and notification_manager.slack.is_configured():
                    if notification_manager.slack.send_notification(
                        "🧪 Test Notification",
                        "This is a test notification from YouTube Playlist Downloader"
                    ):
                        console.print("[green]✓ Test notification sent successfully[/green]")
                    else:
                        console.print("[red]✗ Failed to send test notification[/red]")
    
    def _configure_rate_limiting(self):
        """Configure rate limiting"""
        console.clear()
        console.print(Panel("[bold cyan]Rate Limiting[/bold cyan]", border_style="cyan"))
        
        console.print("\n[yellow]Current Settings:[/yellow]")
        console.print(f"  Max Downloads/Hour: {self.config_manager.config.max_downloads_per_hour}")
        console.print(f"  Min Delay: {self.config_manager.config.min_delay_seconds}s")
        console.print(f"  Max Delay: {self.config_manager.config.max_delay_seconds}s")
        console.print(f"  Bandwidth Limit: {self.config_manager.config.bandwidth_limit_mbps or 'Unlimited'}")
        
        if not Confirm.ask("\nChange rate limiting settings?", default=False):
            return
        
        console.print("\n[dim]Rate limiting helps avoid being blocked by YouTube[/dim]")
        
        self.config_manager.config.max_downloads_per_hour = IntPrompt.ask(
            "\nMaximum downloads per hour",
            default=self.config_manager.config.max_downloads_per_hour
        )
        
        self.config_manager.config.min_delay_seconds = float(Prompt.ask(
            "Minimum delay between downloads (seconds)",
            default=str(self.config_manager.config.min_delay_seconds)
        ))
        
        self.config_manager.config.max_delay_seconds = float(Prompt.ask(
            "Maximum delay between downloads (seconds)",
            default=str(self.config_manager.config.max_delay_seconds)
        ))
        
        if Confirm.ask("\nSet bandwidth limit?", default=False):
            self.config_manager.config.bandwidth_limit_mbps = float(Prompt.ask(
                "Bandwidth limit (Mbps)",
                default=str(self.config_manager.config.bandwidth_limit_mbps or 5.0)
            ))
        else:
            self.config_manager.config.bandwidth_limit_mbps = None
        
        self.config_manager.save_config()
        console.print("\n[green]✓ Rate limiting configured[/green]")
        input("\nPress Enter to continue...")
    
    def _configure_quality_settings(self):
        """Configure quality settings"""
        console.clear()
        console.print(Panel("[bold cyan]Quality Settings[/bold cyan]", border_style="cyan"))
        
        console.print("\n[yellow]Current Settings:[/yellow]")
        console.print(f"  Video Quality: {self.config_manager.config.default_video_quality}")
        console.print(f"  Audio Quality: {self.config_manager.config.default_audio_quality} kbps")
        
        if not Confirm.ask("\nChange quality settings?", default=False):
            return
        
        self.config_manager.config.default_video_quality = Prompt.ask(
            "\nDefault video quality",
            choices=["best", "1080p", "720p", "480p", "360p"],
            default=self.config_manager.config.default_video_quality
        )
        
        self.config_manager.config.default_audio_quality = Prompt.ask(
            "Default audio quality (kbps)",
            choices=["320", "256", "192", "128"],
            default=self.config_manager.config.default_audio_quality
        )
        
        self.config_manager.save_config()
        console.print("\n[green]✓ Quality settings updated[/green]")
        input("\nPress Enter to continue...")
    
    def _configure_storage(self):
        """Configure storage"""
        console.clear()
        console.print(Panel("[bold cyan]Storage Providers[/bold cyan]", border_style="cyan"))
        
        console.print("\n[yellow]Current Settings:[/yellow]")
        console.print(f"  Default Storage: {self.config_manager.config.default_storage.upper()}")
        console.print(f"  Configured Providers: {len(self.config_manager.config.storage_providers)}")
        
        console.print("\n[dim]Storage providers can be configured later from the Settings menu[/dim]")
        console.print("[dim]For now, downloads will be saved locally[/dim]")
        
        if Confirm.ask("\nConfigure cloud storage providers now?", default=False):
            from ui.storage_menu import StorageMenu
            storage_menu = StorageMenu()
            storage_menu.show()
        
        input("\nPress Enter to continue...")


class StatusPage:
    """Display system status"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def show(self):
        """Show status page"""
        console.clear()
        
        header = Panel(
            "[bold cyan]System Status[/bold cyan]",
            border_style="cyan"
        )
        console.print(header)
        
        # Configuration status
        table = Table(title="Configuration", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row(
            "Setup Completed",
            "✓ Yes" if self.config_manager.config.setup_completed else "✗ No"
        )
        table.add_row(
            "Default Video Quality",
            self.config_manager.config.default_video_quality
        )
        table.add_row(
            "Default Audio Quality",
            f"{self.config_manager.config.default_audio_quality} kbps"
        )
        table.add_row(
            "Max Workers",
            str(self.config_manager.config.max_workers)
        )
        table.add_row(
            "Rate Limit",
            f"{self.config_manager.config.max_downloads_per_hour}/hour"
        )
        
        console.print(table)
        
        # Notification status
        notif_table = Table(title="Notifications", show_header=True)
        notif_table.add_column("Provider", style="cyan")
        notif_table.add_column("Status", style="green")
        
        notif_table.add_row(
            "Notifications",
            "✓ Enabled" if self.config_manager.config.notifications_enabled else "✗ Disabled"
        )
        notif_table.add_row(
            "Slack",
            "✓ Enabled" if self.config_manager.config.slack_enabled else "✗ Disabled"
        )
        notif_table.add_row(
            "Email",
            "✓ Enabled" if self.config_manager.config.email_enabled else "✗ Disabled"
        )
        
        console.print("\n")
        console.print(notif_table)
        
        # Storage status
        storage_table = Table(title="Storage", show_header=True)
        storage_table.add_column("Provider", style="cyan")
        storage_table.add_column("Status", style="green")
        
        storage_table.add_row(
            "Default Storage",
            self.config_manager.config.default_storage
        )
        
        provider_count = len(self.config_manager.config.storage_providers)
        storage_table.add_row(
            "Configured Providers",
            str(provider_count)
        )
        
        console.print("\n")
        console.print(storage_table)
