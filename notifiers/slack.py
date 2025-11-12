"""Slack notifier"""
import requests
from typing import Optional

from notifiers.base import BaseNotifier
from rich.console import Console

console = Console()


class SlackNotifier(BaseNotifier):
    """Sends notifications to Slack"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        super().__init__(enabled=bool(webhook_url))
        self.webhook_url = webhook_url
    
    def is_configured(self) -> bool:
        """Check if Slack webhook is configured"""
        return bool(self.webhook_url)
    
    def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Send notification to Slack"""
        if not self.is_configured():
            return False
        
        try:
            color = kwargs.get('color', '#36a64f')  # Default green
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "YouTube Playlist Downloader",
                        "ts": kwargs.get('timestamp', None)
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        
        except Exception as e:
            console.print(f"[red]Failed to send Slack notification: {e}[/red]")
            return False
    
    def notify_download_complete(self, title: str, file_size_mb: float, 
                                 duration_seconds: float) -> bool:
        """Send download complete notification"""
        message = (
            f"*Downloaded:* {title}\n"
            f"*Size:* {file_size_mb:.1f} MB\n"
            f"*Duration:* {self.format_duration(duration_seconds)}"
        )
        return self.send_notification("✅ Download Complete", message, color="#36a64f")
    
    def notify_queue_completed(self, playlist_title: str, 
                              successful: int, total: int) -> bool:
        """Send queue completion notification"""
        success_rate = (successful / total * 100) if total > 0 else 0
        
        message = (
            f"*Playlist:* {playlist_title}\n"
            f"*Completed:* {successful}/{total} videos\n"
            f"*Success Rate:* {success_rate:.1f}%"
        )
        
        color = "#36a64f" if success_rate >= 90 else "#ff9800"
        return self.send_notification("🎬 Queue Complete", message, color=color)
    
    def notify_size_threshold(self, threshold_mb: int, total_mb: float) -> bool:
        """Send size threshold alert"""
        message = (
            f"*Threshold:* {threshold_mb} MB reached\n"
            f"*Total Today:* {total_mb:.1f} MB"
        )
        return self.send_notification("⚠️ Size Threshold Alert", message, color="#ff9800")
    
    def notify_error(self, error_type: str, error_message: str, 
                    context: Optional[str] = None) -> bool:
        """Send error notification"""
        message = f"*Error Type:* {error_type}\n*Message:* {error_message}"
        if context:
            message += f"\n*Context:* {context}"
        return self.send_notification("❌ Error Alert", message, color="#f44336")
