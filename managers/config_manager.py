"""Configuration management"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass
class StorageConfig:
    """Storage provider configuration"""
    enabled: bool = False
    provider_type: str = ""  # ftp, sftp, gdrive, dropbox, onedrive
    
    # FTP/SFTP settings
    host: str = ""
    port: int = 21
    username: str = ""
    password: str = ""
    base_path: str = "/"
    key_filename: Optional[str] = None  # For SFTP
    
    # Cloud storage settings
    credentials_file: Optional[str] = None
    access_token: Optional[str] = None
    folder_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    # Quality override for this storage
    video_quality: Optional[str] = None  # None = use default
    audio_quality: Optional[str] = None  # None = use default
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class AppConfig:
    """Application configuration"""
    cookies_file: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    oauth_expiry: Optional[str] = None
    proxies: List[str] = field(default_factory=list)
    max_workers: int = 3
    default_filename_template: str = "{index:03d} - {title}"
    monitoring_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    download_timeout_minutes: int = 120
    alert_thresholds_mb: List[int] = field(default_factory=lambda: [250, 1000, 5000, 10000])
    
    # Rate limiting
    max_downloads_per_hour: int = 50
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0
    
    # Bandwidth limiting
    bandwidth_limit_mbps: Optional[float] = None
    
    # Live stream settings
    auto_record_live_streams: bool = False
    wait_for_scheduled_streams: bool = False
    max_stream_wait_minutes: int = 60
    
    # Default quality settings
    default_video_quality: str = "720p"
    default_audio_quality: str = "192"
    
    # Filename normalization
    normalize_filenames: bool = True
    
    # Storage providers
    storage_providers: Dict[str, dict] = field(default_factory=dict)
    default_storage: str = "local"  # local, or name of storage provider
    
    # Setup completed flag
    setup_completed: bool = False
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "downloader_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AppConfig.from_dict(data)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
        
        return AppConfig()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
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
