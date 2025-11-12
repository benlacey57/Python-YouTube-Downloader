#!/usr/bin/env python3
"""Send weekly statistics email"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from managers.config_manager import ConfigManager
from managers.stats_manager import StatsManager
from notifiers.email import EmailNotifier

console = Console()


def generate_weekly_stats():
    """Generate and send weekly statistics"""
    console.print("[cyan]Generating weekly statistics...[/cyan]")
    
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
    
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Get stats
    date_range_stats = stats_manager.get_date_range_stats(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    # Calculate totals
    total_downloads = sum(stat.total_downloads for stat in date_range_stats)
    successful_downloads = sum(stat.successful_downloads for stat in date_range_stats)
    total_size_bytes = sum(stat.total_file_size_bytes for stat in date_range_stats)
    queues_completed = sum(stat.queues_completed for stat in date_range_stats)
    
    # Prepare daily stats
    daily_stats = []
    for stat in date_range_stats:
        success_rate = (
            (stat.successful_downloads / stat.total_downloads * 100)
            if stat.total_downloads > 0 else 0
        )
        
        daily_stats.append({
            'date': stat.date,
            'downloads': stat.total_downloads,
            'size_mb': stat.total_file_size_bytes / (1024 * 1024),
            'success_rate': success_rate
        })
    
    # Prepare template data
    stats_data = {
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'total_downloads': total_downloads,
        'successful_downloads': successful_downloads,
        'total_size_gb': total_size_bytes / (1024 * 1024 * 1024),
        'queues_completed': queues_completed,
        'daily_stats': daily_stats,
        'generation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Send email
    console.print("[cyan]Sending weekly statistics email...[/cyan]")
    
    if email_notifier.notify_weekly_stats(stats_data):
        console.print("[green]✓ Weekly statistics sent successfully[/green]")
    else:
        console.print("[red]✗ Failed to send weekly statistics[/red]")


if __name__ == "__main__":
    try:
        generate_weekly_stats()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
