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
from managers.notification_manager import NotificationManager

console = Console()


def generate_daily_summary():
    """Generate and send daily summary"""
    console.print("[cyan]Generating daily summary...[/cyan]")
    
    # Initialize managers
    config_manager = ConfigManager()
    stats_manager = StatsManager()
    notification_manager = NotificationManager(config_manager.config)
    
    if not notification_manager.email or not notification_manager.email.is_configured():
        console.print("[yellow]Email notifications not configured[/yellow]")
        return
    
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
    
    # Get top downloads (if you track this)
    top_downloads = []  # TODO: Add logic to track largest/most recent downloads
    
    # You could query the database for today's completed downloads
    # and get the top 5 by file size or most recent
    try:
        from managers.queue_manager import QueueManager
        queue_manager = QueueManager()
        
        # Get all queues from today
        all_queues = queue_manager.get_all_queues()
        today_str = date.today().strftime("%Y-%m-%d")
        
        for queue in all_queues:
            if queue.completed_at and queue.completed_at.startswith(today_str):
                items = queue_manager.get_queue_items(queue.id)
                for item in items:
                    if item.status == "completed" and item.file_size_bytes:
                        top_downloads.append({
                            'title': item.title,
                            'size_mb': item.file_size_bytes / (1024 * 1024),
                            'duration': notification_manager.email.format_duration(
                                item.download_duration_seconds or 0
                            )
                        })
        
        # Sort by size and get top 5
        top_downloads.sort(key=lambda x: x['size_mb'], reverse=True)
        top_downloads = top_downloads[:5]
    
    except Exception as e:
        console.print(f"[yellow]Could not fetch top downloads: {e}[/yellow]")
        top_downloads = []
    
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
        'top_downloads': top_downloads,
        'generation_time': datetime.now().strftime("%H:%M:%S")
    }
    
    # Send email
    console.print("[cyan]Sending daily summary email...[/cyan]")
    
    if notification_manager.notify_daily_summary(stats_data):
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
