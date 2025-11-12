#!/usr/bin/env python3
"""Send daily summary email"""
import sys
from pathlib import Path
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from managers.config_manager import ConfigManager
from managers.stats_manager import StatsManager
from notifiers.email import EmailNotifier

console = Console()


def generate_daily_summary():
    """Generate and send daily summary"""
    console.print("[cyan]Generating daily summary...[/cyan]")
    
    # Initialize managers
    config_manager = ConfigManager()
    stats_manager = StatsManager()
    
    if not config_manager.config.email_notifications_enabled:
        console.print("[yellow]Email notifications not configured[/yellow]")
        return
    
    # Initialize email notifier
    email_notifier = EmailNotifier(
        smtp_host=config_manager.config.smtp_host,
        smtp_port=config_manager.config.smtp_port,
        smtp_username=config_manager.config.smtp_username,
        smtp_password=config_manager.config.smtp_password,
        from_email=config_manager.config.smtp_from_email,
        to_emails=config_manager.config.smtp_to_emails,
        use_tls=config_manager.config.smtp_use_tls
    )
    
    # Get today's stats
    today_stats = stats_manager.get_today_stats()
    
    # Calculate metrics
    success_rate = (
        (today_stats.successful_downloads / today_stats.total_downloads * 100)
        if today_stats.total_downloads > 0 else 0
    )
    
    avg_file_size_mb = (
        (today_stats.total_file_size_bytes / today_stats.successful_downloads / (1024 * 1024))
        if today_stats.successful_downloads > 0 else 0
    )
    
    # Prepare template data
    stats_data = {
        'date': date.today().strftime("%Y-%m-%d"),
        'total_downloads': today_stats.total_downloads,
        'successful_downloads': today_stats.successful_downloads,
        'failed_downloads': today_stats.failed_downloads,
        'success_rate': success_rate,
        'queues_completed': today_stats.queues_completed,
        'total_size_gb': today_stats.total_file_size_bytes / (1024 * 1024 * 1024),
        'avg_file_size_mb': avg_file_size_mb,
        'top_downloads': [],  # Could add logic to track this
        'generation_time': datetime.now().strftime("%H:%M:%S")
    }
    
    # Send email
    console.print("[cyan]Sending daily summary email...[/cyan]")
    
    if email_notifier.notify_daily_summary(stats_data):
        console.print("[green]✓ Daily summary sent successfully[/green]")
    else:
        console.print("[red]✗ Failed to send daily summary[/red]")


if __name__ == "__main__":
    try:
        generate_daily_summary()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
