"""Slack notification handler"""
import time
from typing import Optional
import requests
from rich.console import Console

console = Console()


class SlackNotifier:
    """Handles Slack notifications"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def is_configured(self) -> bool:
        """Check if Slack webhook is configured"""
        return bool(self.webhook_url)

    def send_notification(self, title: str, message: str, color: str = "good") -> bool:
        """Send a notification to Slack"""
        if not self.is_configured():
            return False

        try:
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "Playlist Downloader",
                        "ts": int(time.time())
                    }
                ]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            console.print(f"[yellow]Failed to send Slack notification: {e}[/yellow]")
            return False

    def notify_queue_completed(self, queue_title: str, completed: int,
                              failed: int, total: int, duration: str) -> bool:
        """Send notification when queue completes"""
        if failed > 0:
            color = "warning"
            status = "Completed with errors"
        else:
            color = "good"
            status = "Completed successfully"

        message = (
            f"*Playlist:* {queue_title}\n"
            f"*Status:* {status}\n"
            f"*Downloaded:* {completed}/{total}\n"
            f"*Failed:* {failed}\n"
            f"*Duration:* {duration}"
        )

        return self.send_notification(f"Queue {status}", message, color)

    def notify_queue_failed(self, queue_title: str, error: str) -> bool:
        """Send notification when queue fails"""
        message = (
            f"*Playlist:* {queue_title}\n"
            f"*Error:* {error}"
        )

        return self.send_notification("Queue Failed", message, "danger")

    def notify_monitoring_update(self, playlist_title: str, new_videos: int) -> bool:
        """Send notification when new videos are detected"""
        message = (
            f"*Playlist:* {playlist_title}\n"
            f"*New Videos:* {new_videos}"
        )

        return self.send_notification("New Videos Detected", message, "#36a64f")

    def notify_size_threshold(self, threshold_mb: int, total_size_mb: float) -> bool:
        """Send notification when size threshold is reached"""
        message = (
            f"*Threshold:* {threshold_mb} MB\n"
            f"*Total Downloaded Today:* {total_size_mb:.2f} MB\n"
            f"*Time:* {time.strftime('%H:%M:%S')}"
        )

        return self.send_notification(
            f"Download Size Alert: {threshold_mb} MB Reached",
            message,
            "warning"
                                )
