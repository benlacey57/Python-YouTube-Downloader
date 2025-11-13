"""Anti-blocking protection measures"""
import random
import time
from typing import List, Optional
from datetime import datetime, timedelta
from rich.console import Console

console = Console()


class AntiBlockingManager:
    """Manage anti-blocking measures"""
    
    def __init__(self, config):
        self.config = config
        self.request_history = []
        self.error_count = 0
        self.last_error_time = None
        self.backoff_until = None
        
        # User agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        self.current_user_agent_index = 0
    
    def can_make_request(self) -> bool:
        """Check if we can make a request based on rate limits"""
        # Check if in backoff period
        if self.backoff_until and datetime.now() < self.backoff_until:
            remaining = (self.backoff_until - datetime.now()).total_seconds()
            console.print(f"[yellow]In backoff period, waiting {remaining:.0f}s[/yellow]")
            return False
        
        # Check hourly rate limit
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old requests
        self.request_history = [
            req_time for req_time in self.request_history
            if req_time > one_hour_ago
        ]
        
        if len(self.request_history) >= self.config.max_downloads_per_hour:
            console.print("[yellow]Hourly rate limit reached[/yellow]")
            return False
        
        return True
    
    def record_request(self):
        """Record a request"""
        self.request_history.append(datetime.now())
    
    def get_delay(self) -> float:
        """Get random delay between requests"""
        return random.uniform(
            self.config.min_delay_seconds,
            self.config.max_delay_seconds
        )
    
    def apply_delay(self):
        """Apply random delay"""
        delay = self.get_delay()
        console.print(f"[dim]Waiting {delay:.1f}s...[/dim]")
        time.sleep(delay)
    
    def get_user_agent(self) -> str:
        """Get current user agent"""
        return self.user_agents[self.current_user_agent_index]
    
    def rotate_user_agent(self):
        """Rotate to next user agent"""
        self.current_user_agent_index = (
            (self.current_user_agent_index + 1) % len(self.user_agents)
        )
    
    def get_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.config.proxies:
            return None
        
        # Simple round-robin
        proxy = random.choice(self.config.proxies)
        return proxy
    
    def record_error(self):
        """Record an error"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        # Exponential backoff
        if self.error_count >= 3:
            backoff_seconds = min(300, 30 * (2 ** (self.error_count - 3)))
            self.backoff_until = datetime.now() + timedelta(seconds=backoff_seconds)
            console.print(f"[red]Multiple errors detected, backing off for {backoff_seconds}s[/red]")
    
    def record_success(self):
        """Record a successful request"""
        # Reset error count on success
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
    
    def get_download_options(self) -> dict:
        """Get yt-dlp options with anti-blocking measures"""
        options = {
            'user_agent': self.get_user_agent(),
            'sleep_interval': self.config.min_delay_seconds,
            'max_sleep_interval': self.config.max_delay_seconds,
            'sleep_interval_requests': 1,
            'sleep_interval_subtitles': 1,
        }
        
        # Add proxy if available
        proxy = self.get_proxy()
        if proxy:
            options['proxy'] = proxy
        
        # Add bandwidth limiting
        if self.config.bandwidth_limit_mbps:
            options['ratelimit'] = int(self.config.bandwidth_limit_mbps * 1024 * 1024 / 8)
        
        return options
