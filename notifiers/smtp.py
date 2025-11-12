"""Email notifier with Jinja2 templates"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from notifiers.base import BaseNotifier
from rich.console import Console

console = Console()


class EmailNotifier(BaseNotifier):
    """Sends email notifications via SMTP"""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587,
                 smtp_username: str = None, smtp_password: str = None,
                 from_email: str = None, to_emails: list = None,
                 use_tls: bool = True):
        super().__init__(enabled=bool(smtp_host and from_email and to_emails))
        
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails or []
        self.use_tls = use_tls
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / 'templates'
        template_dir.mkdir(exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(
            self.smtp_host and 
            self.from_email and 
            self.to_emails
        )
    
    def send_email(self, subject: str, html_content: str, 
                   plain_content: Optional[str] = None) -> bool:
        """Send email via SMTP"""
        if not self.is_configured():
            console.print("[yellow]Email notifier not configured[/yellow]")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Add plain text version if provided
            if plain_content:
                msg.attach(MIMEText(plain_content, 'plain'))
            
            # Add HTML version
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            console.print(f"[green]✓ Email sent: {subject}[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]Failed to send email: {e}[/red]")
            return False
    
    def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Send basic notification email"""
        try:
            template = self.jinja_env.get_template('base.html')
            html = template.render(
                title=title,
                message=message,
                **kwargs
            )
            return self.send_email(title, html, message)
        except Exception as e:
            console.print(f"[red]Failed to render email template: {e}[/red]")
            return False
    
    def notify_download_complete(self, title: str, file_size_mb: float, 
                                 duration_seconds: float) -> bool:
        """Send download complete notification"""
        try:
            template = self.jinja_env.get_template('download_complete.html')
            html = template.render(
                video_title=title,
                file_size_mb=file_size_mb,
                duration=self.format_duration(duration_seconds),
                timestamp=self._get_timestamp()
            )
            return self.send_email(
                f"Download Complete: {title}",
                html,
                f"Downloaded: {title} ({file_size_mb:.1f} MB)"
            )
        except Exception as e:
            console.print(f"[red]Failed to send download notification: {e}[/red]")
            return False
    
    def notify_queue_completed(self, playlist_title: str, 
                              successful: int, total: int) -> bool:
        """Send queue completion notification"""
        try:
            template = self.jinja_env.get_template('queue_complete.html')
            success_rate = (successful / total * 100) if total > 0 else 0
            
            html = template.render(
                playlist_title=playlist_title,
                successful=successful,
                total=total,
                failed=total - successful,
                success_rate=success_rate,
                timestamp=self._get_timestamp()
            )
            return self.send_email(
                f"Queue Complete: {playlist_title}",
                html,
                f"Completed {successful}/{total} videos from {playlist_title}"
            )
        except Exception as e:
            console.print(f"[red]Failed to send queue notification: {e}[/red]")
            return False
    
    def notify_size_threshold(self, threshold_mb: int, total_mb: float) -> bool:
        """Send size threshold alert"""
        try:
            template = self.jinja_env.get_template('threshold_alert.html')
            html = template.render(
                threshold_mb=threshold_mb,
                total_mb=total_mb,
                percentage=(total_mb / threshold_mb * 100) if threshold_mb > 0 else 0,
                timestamp=self._get_timestamp()
            )
            return self.send_email(
                f"Size Threshold Alert: {threshold_mb} MB",
                html,
                f"Downloaded {total_mb:.1f} MB today (threshold: {threshold_mb} MB)"
            )
        except Exception as e:
            console.print(f"[red]Failed to send threshold alert: {e}[/red]")
            return False
    
    def notify_weekly_stats(self, stats_data: Dict[str, Any]) -> bool:
        """Send weekly statistics email"""
        try:
            template = self.jinja_env.get_template('weekly_stats.html')
            html = template.render(**stats_data)
            return self.send_email(
                "Weekly Download Statistics",
                html,
                f"Weekly stats: {stats_data.get('total_downloads', 0)} downloads"
            )
        except Exception as e:
            console.print(f"[red]Failed to send weekly stats: {e}[/red]")
            return False
    
    def notify_daily_summary(self, stats_data: Dict[str, Any]) -> bool:
        """Send daily summary email"""
        try:
            template = self.jinja_env.get_template('daily_summary.html')
            html = template.render(**stats_data)
            return self.send_email(
                f"Daily Summary - {stats_data.get('date', 'Today')}",
                html,
                f"Daily summary: {stats_data.get('total_downloads', 0)} downloads"
            )
        except Exception as e:
            console.print(f"[red]Failed to send daily summary: {e}[/red]")
            return False
    
    def notify_error(self, error_type: str, error_message: str, 
                    context: Optional[str] = None) -> bool:
        """Send error alert"""
        try:
            template = self.jinja_env.get_template('error_alert.html')
            html = template.render(
                error_type=error_type,
                error_message=error_message,
                context=context,
                timestamp=self._get_timestamp()
            )
            return self.send_email(
                f"Error Alert: {error_type}",
                html,
                f"Error: {error_type}\n{error_message}"
            )
        except Exception as e:
            console.print(f"[red]Failed to send error alert: {e}[/red]")
            return False
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
