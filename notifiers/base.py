"""Base notifier with common functionality"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from rich.console import Console

console = Console()


class BaseNotifier(ABC):
    """Abstract base class for all notifiers"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    def is_configured(self) -> bool:
        """Check if notifier is properly configured"""
        return self.enabled
    
    @abstractmethod
    def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Send a basic notification - must be implemented by subclasses"""
        pass
    
    def notify_download_complete(self, title: str, file_size_mb: float, 
                                 duration_seconds: float) -> bool:
        """Notify about completed download"""
        message = (
            f"Downloaded: {title}\n"
            f"Size: {file_size_mb:.1f} MB\n"
            f"Duration: {duration_seconds:.1f}s"
        )
        return self.send_notification("Download Complete", message)
    
    def notify_queue_completed(self, playlist_title: str, 
                              successful: int, total: int) -> bool:
        """Notify about completed queue"""
        message = (
            f"Playlist: {playlist_title}\n"
            f"Completed: {successful}/{total} videos"
        )
        return self.send_notification("Queue Complete", message)
    
    def notify_size_threshold(self, threshold_mb: int, total_mb: float) -> bool:
        """Notify about size threshold reached"""
        message = (
            f"Threshold reached: {threshold_mb} MB\n"
            f"Total downloaded today: {total_mb:.1f} MB"
        )
        return self.send_notification("Size Threshold Alert", message)
    
    def notify_error(self, error_type: str, error_message: str, 
                    context: Optional[str] = None) -> bool:
        """Notify about an error"""
        message = f"Error: {error_type}\n{error_message}"
        if context:
            message += f"\nContext: {context}"
        return self.send_notification("Error Alert", message)
    
    def notify_monitoring_summary(self, channels_checked: int, 
                                 new_videos: int) -> bool:
        """Notify about monitoring check summary"""
        message = (
            f"Checked {channels_checked} channels\n"
            f"Found {new_videos} new videos"
        )
        return self.send_notification("Monitoring Summary", message)
    
    def notify_new_videos(self, channel_name: str, video_count: int) -> bool:
        """Notify about new videos in monitored channel"""
        message = f"Found {video_count} new videos in {channel_name}"
        return self.send_notification("New Videos Available", message)
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def format_file_size(self, bytes_size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
