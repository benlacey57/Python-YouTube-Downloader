"""Abstract base class for all notification handlers"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseNotifier(ABC):
    """
    Abstract base class for notification services (Slack, Email, etc.).
    All concrete notifiers must inherit from this and implement the abstract methods.
    """

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the notification service is properly configured."""
        raise NotImplementedError

    @abstractmethod
    def send_notification(self, title: str, message: str, color: Optional[str] = None) -> bool:
        """Send a general notification."""
        raise NotImplementedError

    @abstractmethod
    def notify_queue_completed(self, queue_title: str, completed: int,
                              failed: int, total: int, duration: str) -> bool:
        """Send notification when a download queue completes."""
        raise NotImplementedError

    @abstractmethod
    def notify_queue_failed(self, queue_title: str, error: str) -> bool:
        """Send notification when a download queue fails completely."""
        raise NotImplementedError

    @abstractmethod
    def notify_monitoring_update(self, playlist_title: str, new_videos: int) -> bool:
        """Send notification when new videos are detected by the monitor."""
        raise NotImplementedError

    @abstractmethod
    def notify_size_threshold(self, threshold_mb: int, total_size_mb: float) -> bool:
        """Send notification when a daily download size threshold is reached."""
        raise NotImplementedError
