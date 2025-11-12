#!/usr/bin/env python3
"""
Automated Cron Script for YouTube Playlist Downloader

This script performs automated operations:
1. Check monitored channels for new videos
2. Download pending queues
3. Send notifications about completed activities

Designed to run via cron for unattended operation.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from managers.config_manager import ConfigManager
from managers.queue_manager import QueueManager
from managers.monitor_manager import MonitorManager
from managers.notification_manager import NotificationManager
from managers.stats_manager import StatsManager
from downloaders.playlist import PlaylistDownloader
from enums import DownloadStatus

console = Console()


class CronJob:
    """Automated cron job handler"""
    
    def __init__(self, log_file: str = "logs/cron.log"):
        """Initialize cron job"""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.monitor_manager = MonitorManager()
        self.queue_manager = QueueManager()
        self.stats_manager = StatsManager()
        self.notification_manager = NotificationManager(self.config_manager.config)
        self.downloader = PlaylistDownloader()
        
        # Statistics for this run
        self.run_stats = {
            'start_time': datetime.now(),
            'channels_checked': 0,
            'new_videos_found': 0,
            'queues_processed': 0,
            'downloads_successful': 0,
            'downloads_failed': 0,
            'errors': []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
        
        # Print to console based on level
        if level == "ERROR":
            console.print(f"[red]{log_message}[/red]")
        elif level == "WARNING":
            console.print(f"[yellow]{log_message}[/yellow]")
        elif level == "SUCCESS":
            console.print(f"[green]{log_message}[/green]")
        else:
            console.print(f"[dim]{log_message}[/dim]")
    
    def check_channels(self) -> int:
        """
        Check all monitored channels for new videos
        
        Returns:
            Number of new videos found
        """
        self.log("=== Starting Channel Monitoring ===")
        
        try:
            channels = self.monitor_manager.get_all_channels()
            monitored = [c for c in channels if c.is_monitored and c.enabled]
            
            if not monitored:
                self.log("No monitored channels found", "WARNING")
                return 0
            
            self.log(f"Checking {len(monitored)} monitored channels")
            
            total_new_videos = 0
            
            for channel in monitored:
                try:
                    self.log(f"Checking channel: {channel.title}")
                    
                    # Check for new videos
                    new_videos = self.monitor_manager.check_channel(channel.id)
                    
                    if new_videos:
                        self.log(f"Found {len(new_videos)} new videos in {channel.title}", "SUCCESS")
                        total_new_videos += len(new_videos)
                        
                        # Send notification
                        if self.notification_manager.has_any_notifier():
                            self.notification_manager.notify_new_videos(
                                channel.title,
                                len(new_videos)
                            )
                    else:
                        self.log(f"No new videos in {channel.title}")
                    
                    self.run_stats['channels_checked'] += 1
                
                except Exception as e:
                    error_msg = f"Error checking channel {channel.title}: {e}"
                    self.log(error_msg, "ERROR")
                    self.run_stats['errors'].append(error_msg)
            
            self.run_stats['new_videos_found'] = total_new_videos
            
            if total_new_videos > 0:
                self.log(f"Total new videos found: {total_new_videos}", "SUCCESS")
            
            # Send monitoring summary
            if self.notification_manager.has_any_notifier() and self.run_stats['channels_checked'] > 0:
                self.notification_manager.notify_monitoring_summary(
                    self.run_stats['channels_checked'],
                    total_new_videos
                )
            
            return total_new_videos
        
        except Exception as e:
            error_msg = f"Channel monitoring failed: {e}"
            self.log(error_msg, "ERROR")
            self.run_stats['errors'].append(error_msg)
            return 0
    
    def process_queues(self, limit: int = None) -> Dict[str, int]:
        """
        Process pending download queues
        
        Args:
            limit: Maximum number of queues to process (None = all)
        
        Returns:
            Dictionary with processing statistics
        """
        self.log("=== Starting Queue Processing ===")
        
        try:
            queues = self.queue_manager.get_all_queues()
            pending = [q for q in queues if q.status == 'pending']
            
            if not pending:
                self.log("No pending queues found")
                return {'processed': 0, 'successful': 0, 'failed': 0}
            
            # Limit queues if specified
            if limit:
                pending = pending[:limit]
                self.log(f"Processing {len(pending)} queues (limited to {limit})")
            else:
                self.log(f"Processing {len(pending)} pending queues")
            
            stats = {'processed': 0, 'successful': 0, 'failed': 0}
            
            for queue in pending:
                try:
                    self.log(f"Processing queue: {queue.playlist_title}")
                    
                    # Get queue items
                    items = self.queue_manager.get_queue_items(queue.id)
                    pending_items = [
                        item for item in items
                        if item.status == DownloadStatus.PENDING.value
                    ]
                    
                    if not pending_items:
                        self.log(f"No pending items in queue: {queue.playlist_title}", "WARNING")
                        continue
                    
                    self.log(f"Downloading {len(pending_items)} items from {queue.playlist_title}")
                    
                    # Download queue (silently, no interactive UI)
                    queue_success = 0
                    queue_failed = 0
                    
                    for idx, item in enumerate(pending_items, 1):
                        try:
                            self.log(f"  [{idx}/{len(pending_items)}] {item.title}")
                            
                            # Download item
                            downloaded_item = self.downloader.download_item(item, queue, idx)
                            self.queue_manager.update_item(downloaded_item)
                            
                            if downloaded_item.status == DownloadStatus.COMPLETED.value:
                                queue_success += 1
                                self.run_stats['downloads_successful'] += 1
                                self.log(f"    ✓ Downloaded successfully", "SUCCESS")
                            else:
                                queue_failed += 1
                                self.run_stats['downloads_failed'] += 1
                                self.log(f"    ✗ Failed: {downloaded_item.error}", "ERROR")
                        
                        except Exception as e:
                            queue_failed += 1
                            self.run_stats['downloads_failed'] += 1
                            error_msg = f"    ✗ Error downloading {item.title}: {e}"
                            self.log(error_msg, "ERROR")
                            self.run_stats['errors'].append(error_msg)
                    
                    # Update queue status
                    if queue_failed == 0:
                        queue.completed_at = datetime.now().isoformat()
                        queue.status = 'completed'
                        self.queue_manager.update_queue(queue)
                        self.queue_manager.clear_queue_resume(queue.id)
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                    
                    stats['processed'] += 1
                    self.run_stats['queues_processed'] += 1
                    
                    # Send queue completion notification
                    if self.notification_manager.has_any_notifier():
                        self.notification_manager.notify_queue_completed(
                            queue.playlist_title,
                            queue_success,
                            len(pending_items)
                        )
                    
                    self.log(f"Queue completed: {queue_success}/{len(pending_items)} successful", "SUCCESS")
                
                except Exception as e:
                    stats['failed'] += 1
                    error_msg = f"Error processing queue {queue.playlist_title}: {e}"
                    self.log(error_msg, "ERROR")
                    self.run_stats['errors'].append(error_msg)
            
            return stats
        
        except Exception as e:
            error_msg = f"Queue processing failed: {e}"
            self.log(error_msg, "ERROR")
            self.run_stats['errors'].append(error_msg)
            return {'processed': 0, 'successful': 0, 'failed': 0}

    def send_summary(self):
        """Send summary notification of this run"""
        if not self.notification_manager.has_any_notifier():
            self.log("No notifiers configured, skipping summary")
            return
        
        end_time = datetime.now()
        duration = (end_time - self.run_stats['start_time']).total_seconds()
        
        # Build summary message
        summary = []
        summary.append(f"🤖 Automated Run Summary")
        summary.append(f"Duration: {duration:.0f}s")
        summary.append("")
        summary.append(f"📺 Channels Checked: {self.run_stats['channels_checked']}")
        summary.append(f"🆕 New Videos Found: {self.run_stats['new_videos_found']}")
        summary.append(f"📥 Queues Processed: {self.run_stats['queues_processed']}")
        summary.append(f"✅ Downloads Successful: {self.run_stats['downloads_successful']}")
        summary.append(f"❌ Downloads Failed: {self.run_stats['downloads_failed']}")
        
        if self.run_stats['errors']:
            summary.append("")
            summary.append(f"⚠️  Errors: {len(self.run_stats['errors'])}")
            for error in self.run_stats['errors'][:5]:  # Show first 5 errors
                summary.append(f"  • {error}")
        
        message = "\n".join(summary)
        
        # Send via Slack
        if self.notification_manager.slack and self.notification_manager.slack.is_configured():
            try:
                color = "#f44336" if self.run_stats['errors'] else "#36a64f"
                self.notification_manager.slack.send_notification(
                    "Automated Run Summary",
                    message,
                    color=color
                )
                self.log("Summary sent via Slack", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to send Slack summary: {e}", "ERROR")
        
        # Send via Email
        if self.notification_manager.email and self.notification_manager.email.is_configured():
            try:
                self.notification_manager.email.send_notification(
                    "Automated Run Summary",
                    message
                )
                self.log("Summary sent via Email", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to send Email summary: {e}", "ERROR")
    
    def run(self, check_channels: bool = True, process_queues: bool = True, 
            queue_limit: int = None, send_summary: bool = True):
        """
        Run the automated cron job
        
        Args:
            check_channels: Check monitored channels for new videos
            process_queues: Process pending download queues
            queue_limit: Maximum number of queues to process
            send_summary: Send summary notification at end
        """
        self.log("=" * 60)
        self.log("AUTOMATED CRON JOB STARTED")
        self.log("=" * 60)
        
        try:
            # Check channels
            if check_channels:
                self.check_channels()
            
            # Process queues
            if process_queues:
                self.process_queues(limit=queue_limit)
            
            # Send summary
            if send_summary:
                self.send_summary()
            
            self.log("=" * 60)
            self.log("AUTOMATED CRON JOB COMPLETED", "SUCCESS")
            self.log("=" * 60)
        
        except Exception as e:
            error_msg = f"Cron job failed: {e}"
            self.log(error_msg, "ERROR")
            
            # Send error notification
            if self.notification_manager.has_any_notifier():
                self.notification_manager.notify_error(
                    "Cron Job Failed",
                    str(e),
                    f"Check logs at {self.log_file}"
                )
            
            sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Automated cron job for YouTube Playlist Downloader'
    )
    
    parser.add_argument(
        '--no-check',
        action='store_true',
        help='Skip checking monitored channels'
    )
    
    parser.add_argument(
        '--no-download',
        action='store_true',
        help='Skip processing download queues'
    )
    
    parser.add_argument(
        '--no-notify',
        action='store_true',
        help='Skip sending summary notification'
    )
    
    parser.add_argument(
        '--queue-limit',
        type=int,
        default=None,
        help='Maximum number of queues to process (default: all)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/cron.log',
        help='Path to log file (default: logs/cron.log)'
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check channels, don\'t download'
    )
    
    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only process downloads, don\'t check channels'
    )
    
    args = parser.parse_args()
    
    # Create cron job
    cron = CronJob(log_file=args.log_file)
    
    # Determine what to run
    check_channels = not args.no_check and not args.download_only
    process_queues = not args.no_download and not args.check_only
    send_summary = not args.no_notify
    
    # Run cron job
    cron.run(
        check_channels=check_channels,
        process_queues=process_queues,
        queue_limit=args.queue_limit,
        send_summary=send_summary
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cron job interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
