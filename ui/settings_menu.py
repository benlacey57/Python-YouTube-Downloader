"""Settings menu"""
from rich.console import Console

console = Console()


class SettingsMenu:
    """Settings configuration menu"""
    
    def __init__(self):
        from managers.config_manager import ConfigManager
        
        self.config_manager = ConfigManager()
    
    def show(self):
        """Display settings menu with enhanced UI"""
        console.print("\n")

        auth_status = "Enabled" if config_manager.config.cookies_file else "Disabled"
        proxy_status = f"{len(config_manager.config.proxies)} proxies" if config_manager.config.proxies else "Disabled"
        slack_status = "Enabled" if config_manager.config.slack_webhook_url else "Disabled"

        settings_table = Table(show_header=False, box=None, padding=(0, 2))
        settings_table.add_column("Setting", style="yellow", no_wrap=True)
        settings_table.add_column("Value", style="white")

        settings_table.add_row("Authentication", auth_status)
        settings_table.add_row("Proxies", proxy_status)
        settings_table.add_row("Parallel Downloads", str(config_manager.config.max_workers))
        settings_table.add_row("Filename Template", config_manager.config.default_filename_template)
        settings_table.add_row("Slack Notifications", slack_status)
        settings_table.add_row("Download Timeout", f"{config_manager.config.download_timeout_minutes} minutes")
        settings_table.add_row("Alert Thresholds (MB)", ", ".join(map(str, config_manager.config.alert_thresholds_mb)))

        settings_panel = Panel(
            settings_table,
            title="[bold]Current Settings[/bold]",
            border_style="cyan"
        )
        console.print(settings_panel)

        options = [
            ("1", "Configure authentication"),
            ("2", "Manage proxies"),
            ("3", "Configure parallel downloads"),
            ("4", "Configure filename template"),
            ("5", "Configure Slack notifications"),
            ("6", "Configure email notifications"),  # NEW
            ("7", "Configure download timeout"),
            ("8", "Configure alert thresholds"),
            ("9", "Configure rate limiting"),
            ("10", "Configure bandwidth limit"),
            ("11", "Configure live streams"),
            ("12", "Configure default quality"),
            ("13", "Configure filename normalization"),
            ("14", "Manage storage providers"),
            ("15", "View system status"),
            ("16", "Seed database"),
            ("17", "Back to main menu")
        ]

        option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
        console.print(f"\n{option_text}\n")

        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=[num for num, _ in options],
            default="8"
        )

        return choice
