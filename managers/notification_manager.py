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
        # Check master switch
        if not self.config.notifications_enabled:
            return
        
        # Initialize Slack if enabled and configured
        if self.config.slack_enabled and self.config.slack_webhook_url:
            self.slack = SlackNotifier(self.config.slack_webhook_url)
            if self.slack.is_configured():
                console.print("[dim]✓ Slack notifications enabled[/dim]")
        
        # Initialize Email if enabled and configured
        if self.config.email_enabled and self.config.smtp_host:
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
        # Check preference
        if not self.config.notify_on_download_complete:
            return False
        
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
        # Check preference
        if not self.config.notify_on_queue_complete:
            return False
        
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
        # Check preference
        if not self.config.notify_on_threshold:
            return False
        
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
        # Check preference
        if not self.config.notify_on_error:
            return False
        
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
    
    def notify_new_videos(self, channel_title: str, video_count: int) -> bool:
        """Notify about new videos found in monitored channel"""
        results = []
        
        message = f"Found {video_count} new video{'s' if video_count != 1 else ''} in {channel_title}"
        
        if self.slack and self.slack.is_configured():
            results.append(self.slack.send_notification(
                f"🆕 New Videos - {channel_title}",
                message,
                color="#2196F3"
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.send_notification(
                f"New Videos - {channel_title}",
                message
            ))
        
        return any(results) if results else False
    
    def notify_monitoring_summary(self, channels_checked: int, 
                                 total_new_videos: int) -> bool:
        """Notify about monitoring check summary"""
        results = []
        
        message = f"Checked {channels_checked} channel{'s' if channels_checked != 1 else ''}\n"
        message += f"Found {total_new_videos} new video{'s' if total_new_videos != 1 else ''} total"
        
        if self.slack and self.slack.is_configured():
            color = "#4CAF50" if total_new_videos > 0 else "#9E9E9E"
            results.append(self.slack.send_notification(
                "📺 Monitoring Check Complete",
                message,
                color=color
            ))
        
        if self.email and self.email.is_configured():
            results.append(self.email.send_notification(
                "Monitoring Check Complete",
                message
            ))
        
        return any(results) if results else False
    
    def send_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """Send daily summary email"""
        if not self.config.send_daily_summary:
            return False
        
        if self.email and self.email.is_configured():
            return self.email.send_daily_summary(stats)
        
        return False
    
    def send_weekly_stats(self, stats: List[Dict[str, Any]]) -> bool:
        """Send weekly statistics email"""
        if not self.config.send_weekly_stats:
            return False
        
        if self.email and self.email.is_configured():
            return self.email.send_weekly_stats(stats)
        
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
