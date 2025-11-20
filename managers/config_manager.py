from dataclasses import dataclass, field, asdict
from typing import Optional, List
import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt

console = Console()


@dataclass
class StorageConfig:
    """Storage provider configuration"""
    provider_type: str  # 'ftp', 'sftp', 'gdrive', 'dropbox', 'onedrive'
    enabled: bool = True
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    key_filename: Optional[str] = None
    base_path: Optional[str] = None
    credentials_file: Optional[str] = None
    access_token: Optional[str] = None
    folder_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    video_quality: Optional[str] = None
    audio_quality: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class AppConfig:
    """Application configuration"""
    # Authentication
    cookies_file: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    
    # Download settings
    max_workers: int = 3
    default_video_quality: str = "720p"
    default_audio_quality: str = "192"
    default_filename_template: str = "{index:03d} - {title}"
    normalize_filenames: bool = True
    download_timeout_minutes: int = 120
    
    # Rate limiting
    max_downloads_per_hour: int = 50
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0
    
    # Bandwidth
    bandwidth_limit_mbps: Optional[float] = None
    
    # Live streams
    auto_record_live_streams: bool = False
    wait_for_scheduled_streams: bool = False
    max_stream_wait_minutes: int = 60

    # Database settings
    database_type: str = "sqlite"  # 'sqlite' or 'mysql'
    database_path: str = "data/downloader.db"  # For SQLite
    database_host: str = "localhost"  # For MySQL
    database_port: int = 3306  # For MySQL
    database_name: str = "downloader"  # For MySQL
    database_user: str = "root"  # For MySQL
    database_password: str = ""  # For MySQL
    
    # Dry run mode
    dry_run: bool = False
    
    # Notifications - General
    notifications_enabled: bool = False
    
    # Notifications - Slack
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    
    # Notifications - Email
    email_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_to_emails: List[str] = field(default_factory=list)
    smtp_use_tls: bool = True
    email_notifications_enabled: bool = False  # Deprecated - use email_enabled
    
    # Notification preferences - what to notify about
    notify_on_download_complete: bool = True  # NEW
    notify_on_queue_complete: bool = True  # NEW
    notify_on_error: bool = True  # NEW
    notify_on_threshold: bool = True  # NEW
    
    # Daily/weekly email settings
    send_daily_summary: bool = False
    send_weekly_stats: bool = False
    daily_summary_time: str = "18:00"
    weekly_stats_day: int = 0  # Monday
    
    # Alert thresholds
    alert_thresholds_mb: List[int] = field(default_factory=lambda: [250, 1000, 5000, 10000])
    
    # Proxies
    proxies: List[str] = field(default_factory=list)
    proxy_rotation_enabled: bool = False
    proxy_rotation_frequency: int = 10  # Change proxy every X downloads
    
    # Storage
    default_storage: str = "local"
    storage_providers: dict = field(default_factory=dict)
    
    # Setup
    setup_completed: bool = False


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "downloader_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Migrate old field name to new one
                if 'download_timeout_seconds' in data:
                    # Convert seconds to minutes (default was 300 seconds = 5 minutes)
                    data['download_timeout_minutes'] = data.pop('download_timeout_seconds') // 60
                    if data['download_timeout_minutes'] < 30:
                        data['download_timeout_minutes'] = 120  # Use safer default
                
                return AppConfig(**data)
            except Exception as e:
                console.print(f"[yellow]Error loading config: {e}[/yellow]")
                console.print("[yellow]Using default configuration[/yellow]")
                return AppConfig()
        return AppConfig()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            console.print("[green]✓ Configuration saved[/green]")
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
            
    def configure_default_quality(self):
        """Configure default quality settings"""
        console.print("\n[cyan]Default Quality Configuration[/cyan]")
        console.print(f"\nCurrent settings:")
        console.print(f"  • Video: {self.config.default_video_quality}")
        console.print(f"  • Audio: {self.config.default_audio_quality}kbps")
        
        # Video quality
        console.print("\n[cyan]Default Video Quality:[/cyan]")
        video_qualities = ["best", "1080p", "720p", "480p", "360p", "worst"]
        
        for idx, quality in enumerate(video_qualities, 1):
            console.print(f"  {idx}. {quality}")
        
        video_choice = Prompt.ask(
            "Select default video quality",
            choices=[str(i) for i in range(1, len(video_qualities) + 1)],
            default="3"  # 720p
        )
        
        self.config.default_video_quality = video_qualities[int(video_choice) - 1]
        
        # Audio quality
        console.print("\n[cyan]Default Audio Quality:[/cyan]")
        audio_qualities = [("320", "320kbps (High)"), ("192", "192kbps (Standard)"), ("128", "128kbps (Low)")]
        
        for idx, (value, desc) in enumerate(audio_qualities, 1):
            console.print(f"  {idx}. {desc}")
        
        audio_choice = Prompt.ask(
            "Select default audio quality",
            choices=[str(i) for i in range(1, len(audio_qualities) + 1)],
            default="2"  # 192kbps
        )
        
        self.config.default_audio_quality = audio_qualities[int(audio_choice) - 1][0]
        
        console.print(f"\n[green]✓ Default qualities set:[/green]")
        console.print(f"  • Video: {self.config.default_video_quality}")
        console.print(f"  • Audio: {self.config.default_audio_quality}kbps")
        
        self.save_config()

        
    def configure_notification_preferences(self):
        """Configure which events trigger notifications"""
        console.print("\n[cyan]Notification Preferences[/cyan]")
        console.print("Choose which events should trigger notifications:\n")
    
        self.config.notify_on_download_complete = Confirm.ask(
            "Notify on individual download complete?",
            default=self.config.notify_on_download_complete
        )
    
        self.config.notify_on_queue_complete = Confirm.ask(
            "Notify on queue complete?",
            default=self.config.notify_on_queue_complete
        )
    
        self.config.notify_on_error = Confirm.ask(
            "Notify on errors?",
            default=self.config.notify_on_error
        )
    
        self.config.notify_on_threshold = Confirm.ask(
            "Notify on size thresholds?",
            default=self.config.notify_on_threshold
        )
    
        self.save_config()
        console.print("\n[green]✓ Notification preferences updated[/green]")

    def toggle_notification_provider(self):
        """Toggle notification providers on/off"""
        console.print("\n[cyan]Notification Providers[/cyan]")
    
        console.print(f"\n[cyan]Slack:[/cyan] {'[green]Enabled[/green]' if self.config.slack_enabled else '[red]Disabled[/red]'}")
        if self.config.slack_webhook_url:
            console.print(f"  Webhook: {self.config.slack_webhook_url[:50]}...")
    
        console.print(f"\n[cyan]Email:[/cyan] {'[green]Enabled[/green]' if self.config.email_enabled else '[red]Disabled[/red]'}")
        if self.config.smtp_host:
            console.print(f"  SMTP Host: {self.config.smtp_host}")
            console.print(f"  From: {self.config.smtp_from_email}")
            console.print(f"  To: {', '.join(self.config.smtp_to_emails)}")
    
        console.print("\n[yellow]Options:[/yellow]")
        console.print("  1. Toggle Slack")
        console.print("  2. Toggle Email")
        console.print("  3. Back")
    
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"], default="3")
    
        if choice == "1":
            if not self.config.slack_webhook_url:
                console.print("[yellow]Slack webhook not configured. Configure it first.[/yellow]")
                if Confirm.ask("Configure now?", default=True):
                    self.configure_slack_webhook()
            else:
                self.config.slack_enabled = not self.config.slack_enabled
                status = "enabled" if self.config.slack_enabled else "disabled"
                console.print(f"[green]✓ Slack notifications {status}[/green]")
                self.save_config()
    
        elif choice == "2":
            if not self.config.smtp_host:
                console.print("[yellow]Email not configured. Configure it first.[/yellow]")
                if Confirm.ask("Configure now?", default=True):
                    self.configure_email_notifications()
            else:
                self.config.email_enabled = not self.config.email_enabled
                status = "enabled" if self.config.email_enabled else "disabled"
                console.print(f"[green]✓ Email notifications {status}[/green]")
                self.save_config()

    def configure_email_notifications(self):
        """Configure email notifications"""
        console.print("\n[cyan]Email Notification Configuration[/cyan]")
    
        console.print("\n[yellow]SMTP Server Settings:[/yellow]")
        console.print("Common providers:")
        console.print("  Gmail: smtp.gmail.com:587")
        console.print("  Outlook: smtp-mail.outlook.com:587")
        console.print("  Yahoo: smtp.mail.yahoo.com:587")
    
        self.config.smtp_host = Prompt.ask("\nSMTP Host")
        self.config.smtp_port = IntPrompt.ask("SMTP Port", default=587)
        self.config.smtp_username = Prompt.ask("SMTP Username (email)")
        self.config.smtp_password = Prompt.ask("SMTP Password", password=True)
        self.config.smtp_from_email = Prompt.ask("From Email", default=self.config.smtp_username)
    
        # To emails
        console.print("\n[yellow]Recipient Email(s):[/yellow]")
        to_emails = Prompt.ask("To Email(s) (comma-separated)")
        self.config.smtp_to_emails = [email.strip() for email in to_emails.split(',')]
    
        self.config.smtp_use_tls = Confirm.ask("Use TLS?", default=True)
        self.config.email_enabled = True
        self.config.notifications_enabled = True
    
        # Daily/Weekly summaries
        console.print("\n[yellow]Automated Reports:[/yellow]")
        self.config.send_daily_summary = Confirm.ask("Send daily summary?", default=True)
        self.config.send_weekly_stats = Confirm.ask("Send weekly statistics?", default=True)
    
        if self.config.send_daily_summary:
            self.config.daily_summary_time = Prompt.ask(
                "Daily summary time (HH:MM)",
                default="18:00"
            )
    
        self.save_config()
    
        console.print("\n[green]✓ Email notifications configured[/green]")
    
        # Test email
        if Confirm.ask("\nSend test email?", default=True):
            from managers.notification_manager import NotificationManager
        
            notification_manager = NotificationManager(self.config)
        
            if notification_manager.email and notification_manager.email.is_configured():
                if notification_manager.email.send_notification(
                        "Test YouTube Downloader Email",
                        "This is a test email from YouTube Playlist Downloader"
                    ):
                    console.print("[green]✓ Test email sent successfully[/green]")
                else:
                    console.print("[red]✗ Failed to send test email[/red]")
                
    def configure_filename_normalization(self):
        """Configure filename normalization"""
        console.print("\n[cyan]Filename Normalization[/cyan]")
        console.print(f"\nCurrent: {'Enabled' if self.config.normalize_filenames else 'Disabled'}")
        console.print("\nWhen enabled, filenames will be:")
        console.print("  • Converted to sentence case")
        console.print("  • Special characters removed")
        console.print("  • Emojis removed")
        console.print("  • Whitespace normalized")
        
        self.config.normalize_filenames = Confirm.ask(
            "\nEnable filename normalization?",
            default=self.config.normalize_filenames
        )
        
        status = "enabled" if self.config.normalize_filenames else "disabled"
        console.print(f"\n[green]✓ Filename normalization {status}[/green]")
        self.save_config()
    
    def add_storage_provider(self, name: str, config: StorageConfig):
        """Add a storage provider"""
        self.config.storage_providers[name] = config.to_dict()
        self.save_config()
    
    def remove_storage_provider(self, name: str):
        """Remove a storage provider"""
        if name in self.config.storage_providers:
            del self.config.storage_providers[name]
            
            # Reset default if it was the default
            if self.config.default_storage == name:
                self.config.default_storage = "local"
            
            self.save_config()
    
    def get_storage_provider(self, name: str) -> Optional[StorageConfig]:
        """Get a storage provider configuration"""
        if name in self.config.storage_providers:
            return StorageConfig.from_dict(self.config.storage_providers[name])
        return None
    
    def list_storage_providers(self) -> List[str]:
        """List all configured storage providers"""
        return list(self.config.storage_providers.keys())
    
    def set_default_storage(self, name: str):
        """Set default storage provider"""
        if name == "local" or name in self.config.storage_providers:
            self.config.default_storage = name
            self.save_config()
    
    # Previous methods continue...
    def configure_authentication(self):
        """Configure authentication settings"""
        console.print("\n[cyan]Authentication Configuration[/cyan]")
        console.print("\nAuthentication methods:")
        console.print("  1. Browser cookies (cookies.txt) - Recommended")
        console.print("  2. OAuth2 (Complex setup required)\n")
        
        method = Prompt.ask("Select method", choices=["1", "2"], default="1")
        
        if method == "1":
            self._configure_cookies()
        else:
            self._configure_oauth()
    
    def _configure_cookies(self):
        """Configure cookie-based authentication"""
        console.print("\n[yellow]To export cookies:[/yellow]")
        console.print("1. Install browser extension:")
        console.print("   Chrome: 'Get cookies.txt LOCALLY'")
        console.print("   Firefox: 'cookies.txt'")
        console.print("2. Navigate to YouTube whilst logged in")
        console.print("3. Export cookies to a file")
        console.print("4. Enter the file path below\n")
        
        cookies_file = Prompt.ask("Cookies file path (or leave blank to skip)", default="")
        
        if cookies_file and Path(cookies_file).exists():
            self.config.cookies_file = cookies_file
            self.config.oauth_token = None
            console.print("[green]✓ Cookie authentication configured[/green]")
        elif cookies_file:
            console.print("[yellow]Warning: File not found, skipping[/yellow]")
        else:
            self.config.cookies_file = None
        
        self.save_config()
    
    def _configure_oauth(self):
        """Configure OAuth authentication"""
        console.print("\n[yellow]OAuth setup requires Google Cloud credentials[/yellow]")
        console.print("[yellow]This is a placeholder for full OAuth2 implementation[/yellow]")
        console.print("[yellow]Falling back to cookies.txt method[/yellow]\n")
    
    def configure_filename_template(self):
        """Configure default filename template"""
        console.print("\n[cyan]Filename Template Configuration[/cyan]")
        console.print(f"\nCurrent template: {self.config.default_filename_template}")
        console.print("\nAvailable placeholders:")
        console.print("  {title} - Video title")
        console.print("  {uploader} - Channel/uploader name")
        console.print("  {date} - Upload date")
        console.print("  {index} - Position in playlist")
        console.print("  {index:03d} - Zero-padded index (001, 002, etc.)")
        console.print("  {playlist} - Playlist name")
        console.print("  {video_id} - YouTube video ID\n")
        
        console.print("Example templates:")
        console.print("  {index:03d} - {title}")
        console.print("  {playlist} - {index:02d} - {title}")
        console.print("  {date} - {uploader} - {title}")
        console.print("  {title} [{video_id}]\n")
        
        template = Prompt.ask(
            "Enter template",
            default=self.config.default_filename_template
        )
        
        self.config.default_filename_template = template
        self.save_config()
        console.print("[green]✓ Template configured[/green]")
    
    def configure_slack(self):
        """Configure Slack webhook"""
        console.print("\n[cyan]Slack Notifications Configuration[/cyan]")
        console.print("\nTo get a Slack webhook URL:")
        console.print("  1. Go to https://api.slack.com/apps")
        console.print("  2. Create a new app or select existing")
        console.print("  3. Enable 'Incoming Webhooks'")
        console.print("  4. Add webhook to workspace")
        console.print("  5. Copy the webhook URL\n")
        
        if self.config.slack_webhook_url:
            console.print(f"[green]Current webhook:[/green] {self.config.slack_webhook_url[:50]}...")
            if Confirm.ask("Update webhook URL?", default=False):
                webhook = Prompt.ask("Slack webhook URL (or leave blank to disable)", default="")
                self.config.slack_webhook_url = webhook if webhook else None
        else:
            webhook = Prompt.ask("Slack webhook URL (or leave blank to skip)", default="")
            self.config.slack_webhook_url = webhook if webhook else None
        
        self.save_config()
        
        if self.config.slack_webhook_url:
            console.print("[green]✓ Slack notifications configured[/green]")
        else:
            console.print("[yellow]Slack notifications disabled[/yellow]")
    
    def configure_workers(self):
        """Configure parallel download workers"""
        console.print("\n[cyan]Parallel Downloads Configuration[/cyan]")
        console.print(f"\nCurrent: {self.config.max_workers} parallel downloads")
        console.print("\nRecommendations:")
        console.print("  • 1-2 workers: Slow connection or rate limit concerns")
        console.print("  • 3-4 workers: Balanced (recommended)")
        console.print("  • 5+ workers: Fast connection, may trigger rate limits\n")
        
        workers = IntPrompt.ask(
            "Number of parallel downloads",
            default=self.config.max_workers
        )
        
        self.config.max_workers = max(1, min(10, workers))
        console.print(f"[green]✓ Set to {self.config.max_workers} workers[/green]")
        self.save_config()
    
    def configure_timeout(self):
        """Configure download timeout for long videos"""
        console.print("\n[cyan]Download Timeout Configuration[/cyan]")
        console.print(f"\nCurrent timeout: {self.config.download_timeout_minutes} minutes")
        console.print("\nRecommendations:")
        console.print("  • 60 minutes: Short videos only")
        console.print("  • 120 minutes: Standard (1-2 hour videos)")
        console.print("  • 240+ minutes: Long videos (4+ hours)\n")
        
        timeout = IntPrompt.ask(
            "Timeout in minutes",
            default=self.config.download_timeout_minutes
        )
        
        self.config.download_timeout_minutes = max(30, min(480, timeout))
        console.print(f"[green]✓ Set timeout to {self.config.download_timeout_minutes} minutes[/green]")
        self.save_config()
    
    def configure_alert_thresholds(self):
        """Configure download size alert thresholds"""
        console.print("\n[cyan]Download Size Alert Configuration[/cyan]")
        console.print(f"\nCurrent thresholds (MB): {', '.join(map(str, self.config.alert_thresholds_mb))}")
        console.print("\nDefault thresholds:")
        console.print("  • 250 MB - Quarter gigabyte")
        console.print("  • 1000 MB (1 GB) - One gigabyte")
        console.print("  • 5000 MB (5 GB) - Five gigabytes")
        console.print("  • 10000 MB (10 GB) - Ten gigabytes\n")
        
        if Confirm.ask("Reset to defaults?", default=False):
            self.config.alert_thresholds_mb = [250, 1000, 5000, 10000]
        else:
            console.print("\nEnter comma-separated values in MB (e.g., 250,1000,5000)")
            thresholds_str = Prompt.ask(
                "Thresholds",
                default=",".join(map(str, self.config.alert_thresholds_mb))
            )
            try:
                self.config.alert_thresholds_mb = [
                    int(t.strip()) for t in thresholds_str.split(',') if t.strip()
                ]
            except ValueError:
                console.print("[red]Invalid format, keeping current values[/red]")
        
        self.save_config()
        console.print(f"[green]✓ Thresholds set to: {', '.join(map(str, self.config.alert_thresholds_mb))} MB[/green]")
    
    def configure_rate_limiting(self):
        """Configure rate limiting settings"""
        console.print("\n[cyan]Rate Limiting Configuration[/cyan]")
        console.print(f"\nCurrent settings:")
        console.print(f"  • Max downloads per hour: {self.config.max_downloads_per_hour}")
        console.print(f"  • Min delay: {self.config.min_delay_seconds}s")
        console.print(f"  • Max delay: {self.config.max_delay_seconds}s")
        
        console.print("\n[yellow]Rate limiting helps avoid IP bans and rate limits[/yellow]")
        console.print("\nRecommendations:")
        console.print("  • Conservative: 30 downloads/hour, 3-7s delay")
        console.print("  • Moderate: 50 downloads/hour, 2-5s delay")
        console.print("  • Aggressive: 100 downloads/hour, 1-3s delay\n")
        
        max_per_hour = IntPrompt.ask(
            "Max downloads per hour",
            default=self.config.max_downloads_per_hour
        )
        
        min_delay = Prompt.ask(
            "Min delay between downloads (seconds)",
            default=str(self.config.min_delay_seconds)
        )
        
        max_delay = Prompt.ask(
            "Max delay between downloads (seconds)",
            default=str(self.config.max_delay_seconds)
        )
        
        try:
            self.config.max_downloads_per_hour = max(1, min(200, max_per_hour))
            self.config.min_delay_seconds = float(min_delay)
            self.config.max_delay_seconds = float(max_delay)
            
            if self.config.min_delay_seconds > self.config.max_delay_seconds:
                self.config.min_delay_seconds, self.config.max_delay_seconds = \
                    self.config.max_delay_seconds, self.config.min_delay_seconds
            
            console.print(f"\n[green]✓ Rate limiting configured:[/green]")
            console.print(f"  • {self.config.max_downloads_per_hour} downloads/hour")
            console.print(f"  • {self.config.min_delay_seconds}s - {self.config.max_delay_seconds}s random delay")
            
            self.save_config()
        except ValueError:
            console.print("[red]Invalid values entered[/red]")
    
    def configure_bandwidth_limit(self):
        """Configure bandwidth limiting"""
        console.print("\n[cyan]Bandwidth Limiting Configuration[/cyan]")
        
        if self.config.bandwidth_limit_mbps:
            console.print(f"\nCurrent limit: {self.config.bandwidth_limit_mbps} Mbps")
        else:
            console.print("\nCurrent limit: Unlimited")
        
        console.print("\nCommon limits:")
        console.print("  • 1 Mbps (slow)")
        console.print("  • 5 Mbps (moderate)")
        console.print("  • 10 Mbps (fast)")
        console.print("  • 25+ Mbps (very fast)\n")
        
        if Confirm.ask("Enable bandwidth limiting?", default=self.config.bandwidth_limit_mbps is not None):
            limit_str = Prompt.ask(
                "Bandwidth limit in Mbps",
                default=str(self.config.bandwidth_limit_mbps or "5")
            )
            
            try:
                limit = float(limit_str)
                if limit <= 0:
                    console.print("[red]Limit must be positive[/red]")
                    return
                
                self.config.bandwidth_limit_mbps = limit
                console.print(f"[green]✓ Bandwidth limited to {limit} Mbps[/green]")
            except ValueError:
                console.print("[red]Invalid value[/red]")
                return
        else:
            self.config.bandwidth_limit_mbps = None
            console.print("[yellow]Bandwidth limiting disabled[/yellow]")
        
        self.save_config()
    
    def configure_live_streams(self):
        """Configure live stream settings"""
        console.print("\n[cyan]Live Stream Configuration[/cyan]")
        console.print(f"\nCurrent settings:")
        console.print(f"  • Auto-record: {self.config.auto_record_live_streams}")
        console.print(f"  • Wait for scheduled: {self.config.wait_for_scheduled_streams}")
        console.print(f"  • Max wait time: {self.config.max_stream_wait_minutes} minutes")
        
        self.config.auto_record_live_streams = Confirm.ask(
            "\nAutomatically record live streams?",
            default=self.config.auto_record_live_streams
        )
        
        if self.config.auto_record_live_streams:
            self.config.wait_for_scheduled_streams = Confirm.ask(
                "Wait for scheduled streams to start?",
                default=self.config.wait_for_scheduled_streams
            )
            
            if self.config.wait_for_scheduled_streams:
                max_wait = IntPrompt.ask(
                    "Max wait time (minutes)",
                    default=self.config.max_stream_wait_minutes
                )
                self.config.max_stream_wait_minutes = max(1, min(480, max_wait))
        
        console.print(f"\n[green]✓ Live stream settings configured[/green]")
        self.save_config()
    
    def configure_parallel_downloads(self):
        """Alias for configure_workers for menu compatibility"""
        self.configure_workers()
    
    def manage_proxies(self):
        """Manage proxy settings - delegates to network settings menu"""
        from ui.network_settings_menu import NetworkSettingsMenu
        network_menu = NetworkSettingsMenu(self)
        network_menu.show()
    
    def configure_slack_webhook(self):
        """Alias for configure_slack for menu compatibility"""
        self.configure_slack()
