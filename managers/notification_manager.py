"""Notification manager for handling all notifiers"""
from typing import Optional, List, Dict, Any
from rich.console import Console

from managers.config_manager import AppConfig
from notifiers.slack import SlackNotifier
from notifiers.email import EmailNotifier

console = Console()


class NotificationManager:
    """Manages all notification providers"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.slack = None
        self.email = None
        
        # Initialize enabled notifiers
        self._initialize_notifiers()
    
    def _initialize_notifiers(self):
        """Initialize all configured notifiers"""
        # Initialize Slack if configured
        if self.config.slack_webhook_url:
            self.slack = SlackNotifier(self.config.slack_webhook_url)
            if self.slack.is_configured():
                console.print("[dim]✓ Slack notifications enabled[/dim]")
        
        # Initialize Email if configured
        if self.config.email_notifications_enabled:
            self.email = EmailNotifier(
                smtp_host=self.config.smtp_host,
                smtp_port=self.config.smtp_port,
                smtp_username=self.config.smtp_username,
                smtp_password=self.config.smtp_password,
                from_email=self.config.smtp_from_email,
                to_emails=self.config.smtp_to_emails,
                use_tls=self.config.smtp_use_tls
            )
            if self.email.is_configured():
                console.print("[dim]✓ Email notifications enabled[/dim]")
    
    def has_any_notifier(self) -> bool:
        """Check if any notifier is configured"""
        return (
            (self.slack and self.slack.is_configured()) or
            (self.email and self.email.is_configured())
        )
    
    def notify_download_complete(self, title: str, file_size_mb: float, 
                                 duration_seconds: float) -> bool:
        """Notify all configured notifiers about download completion"""
        results = []
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.notify_download_complete(
                title, file_size_mb, duration_seconds
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.notify_download_complete(
                title, file_size_mb, duration_seconds
            ))
        
        return any(results) if results else False
    
    def notify_queue_completed(self, playlist_title: str, 
                              successful: int, total: int) -> bool:
        """Notify all configured notifiers about queue completion"""
        results = []
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.notify_queue_completed(
                playlist_title, successful, total
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.notify_queue_completed(
                playlist_title, successful, total
            ))
        
        return any(results) if results else False
    
    def notify_size_threshold(self, threshold_mb: int, total_mb: float) -> bool:
        """Notify all configured notifiers about size threshold"""
        results = []
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.notify_size_threshold(
                threshold_mb, total_mb
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.notify_size_threshold(
                threshold_mb, total_mb
            ))
        
        return any(results) if results else False
    
    def notify_error(self, error_type: str, error_message: str, 
                    context: Optional[str] = None) -> bool:
        """Notify all configured notifiers about an error"""
        results = []
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.notify_error(
                error_type, error_message, context
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.notify_error(
                error_type, error_message, context
            ))
        
        return any(results) if results else False
    
    def notify_monitoring_summary(self, channels_checked: int, 
                                 new_videos: int) -> bool:
        """Notify all configured notifiers about monitoring summary"""
        results = []
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.notify_monitoring_summary(
                channels_checked, new_videos
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.notify_monitoring_summary(
                channels_checked, new_videos
            ))
        
        return any(results) if results else False
    
    def notify_new_videos(self, channel_name: str, video_count: int) -> bool:
        """Notify all configured notifiers about new videos"""
        results = []
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.notify_new_videos(
                channel_name, video_count
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.notify_new_videos(
                channel_name, video_count
            ))
        
        return any(results) if results else False
    
    def notify_weekly_stats(self, stats_data: Dict[str, Any]) -> bool:
        """Send weekly statistics (email only)"""
        if self.email and self.email.is_configured():
            return self.email.notify_weekly_stats(stats_data)
        return False
    
    def notify_daily_summary(self, stats_data: Dict[str, Any]) -> bool:
        """Send daily summary (email only)"""
        if self.email and self.email.is_configured():
            return self.email.notify_daily_summary(stats_data)
        return False
    
    def reload_config(self, config: AppConfig):
        """Reload notifiers with new configuration"""
        self.config = config
        self.slack = None
        self.email = None
        self._initialize_notifiers()
    
    def get_status(self) -> Dict[str, bool]:
        """Get status of all notifiers"""
        return {
            'slack_configured': self.slack is not None and self.slack.is_configured(),
            'email_configured': self.email is not None and self.email.is_configured(),
            'any_configured': self.has_any_notifier()
        }
