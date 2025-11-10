"""Configuration management"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

console = Console()


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
