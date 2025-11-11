"""SMTP (Email) notification handler"""
import time
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Dict
from rich.console import Console

# Import the new BaseNotifier
from notifiers.base_notifier import BaseNotifier 

console = Console()

class SMTPNotifier(BaseNotifier):
    """Handles SMTP (Email) notifications"""

    def __init__(self, smtp_config: Dict):
        """
        Initialize with SMTP configuration.
        smtp_config is expected to contain:
        'host', 'port', 'user', 'password', 'sender_email', 'recipient_email', 'use_tls'
        """
        self.config = smtp_config

    def is_configured(self) -> bool:
        """Check if all required SMTP credentials are present."""
        required_keys = ['host', 'port', 'user', 'password', 'sender_email', 'recipient_email']
        return all(self.config.get(k) for k in required_keys)

    def send_notification(self, title: str, message: str, color: Optional[str] = None) -> bool:
        """Send a general notification via SMTP."""
        if not self.is_configured():
            return False

        msg = MIMEText(message, 'plain')
        msg['Subject'] = f"[PD] {title}"
        msg['From'] = self.config['sender_email']
        msg['To'] = self.config['recipient_email']
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.config['host'], self.config['port'], timeout=10)
            
            if self.config.get('use_tls', True):
                server.starttls()
            
            # Login
            server.login(self.config['user'], self.config['password'])
            
            # Send Email
            server.sendmail(self.config['sender_email'], self.config['recipient_email'], msg.as_string())
            server.quit()
            
            return True

        except Exception as e:
            console.print(f"[yellow]Failed to send SMTP notification: {e}[/yellow]")
            return False

    def notify_queue_completed(self, queue_title: str, completed: int,
                              failed: int, total: int, duration: str) -> bool:
        """Send notification when queue completes"""
        if failed > 0:
            status = "Completed with errors"
        else:
            status = "Completed successfully"

        title = f"Queue {status}: {queue_title}"
        message = (
            f"Playlist: {queue_title}\n"
            f"Status: {status}\n"
            f"Downloaded: {completed}/{total}\n"
            f"Failed: {failed}\n"
            f"Duration: {duration}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return self.send_notification(title, message)

    def notify_queue_failed(self, queue_title: str, error: str) -> bool:
        """Send notification when queue fails"""
        title = f"Queue Failed: {queue_title}"
        message = (
            f"Playlist: {queue_title}\n"
            f"Error: {error}"
        )
        return self.send_notification(title, message)

    def notify_monitoring_update(self, playlist_title: str, new_videos: int) -> bool:
        """Send notification when new videos are detected"""
        title = "New Videos Detected"
        message = (
            f"Playlist: {playlist_title}\n"
            f"New Videos: {new_videos}"
        )
        return self.send_notification(title, message)

    def notify_size_threshold(self, threshold_mb: int, total_size_mb: float) -> bool:
        """Send notification when size threshold is reached"""
        title = f"Download Size Alert: {threshold_mb} MB Reached"
        message = (
            f"Threshold: {threshold_mb} MB\n"
            f"Total Downloaded Today: {total_size_mb:.2f} MB\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return self.send_notification(title, message)
