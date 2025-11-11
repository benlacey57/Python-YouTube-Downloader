"""Rate limiting for downloads"""
import time
from datetime import datetime, timedelta
from typing import List
from rich.console import Console
import random

console = Console()


class RateLimiter:
    """Rate limiter to prevent IP bans"""
    
    def __init__(self, max_downloads_per_hour: int = 50, 
                 min_delay_seconds: float = 2.0, 
                 max_delay_seconds: float = 5.0):
        self.max_downloads_per_hour = max_downloads_per_hour
        self.min_delay_seconds = min_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.download_timestamps: List[datetime] = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        # Clean old timestamps (older than 1 hour)
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        self.download_timestamps = [
            ts for ts in self.download_timestamps 
            if ts > one_hour_ago
        ]
        
        # Check if we've hit the limit
        if len(self.download_timestamps) >= self.max_downloads_per_hour:
            # Wait until the oldest download is more than 1 hour old
            oldest = self.download_timestamps[0]
            wait_until = oldest + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()
            
            if wait_seconds > 0:
                console.print(f"\n[yellow]Rate limit reached. Waiting {wait_seconds:.0f} seconds...[/yellow]")
                time.sleep(wait_seconds)
                # Clean timestamps again after waiting
                now = datetime.now()
                one_hour_ago = now - timedelta(hours=1)
                self.download_timestamps = [
                    ts for ts in self.download_timestamps 
                    if ts > one_hour_ago
                ]
        
        # Random delay between downloads
        delay = random.uniform(self.min_delay_seconds, self.max_delay_seconds)
        if delay > 0:
            time.sleep(delay)
        
        # Record this download
        self.download_timestamps.append(datetime.now())
    
    def get_stats(self) -> dict:
        """Get current rate limit statistics"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old timestamps
        self.download_timestamps = [
            ts for ts in self.download_timestamps 
            if ts > one_hour_ago
        ]
        
        downloads_this_hour = len(self.download_timestamps)
        remaining = self.max_downloads_per_hour - downloads_this_hour
        
        return {
            'downloads_this_hour': downloads_this_hour,
            'max_per_hour': self.max_downloads_per_hour,
            'remaining': max(0, remaining),
            'percentage_used': (downloads_this_hour / self.max_downloads_per_hour * 100)
        }
    
    def reset(self):
        """Reset rate limiter"""
        self.download_timestamps = []
    
    def set_limits(self, max_per_hour: int = None, 
                   min_delay: float = None, 
                   max_delay: float = None):
        """Update rate limit settings"""
        if max_per_hour is not None:
            self.max_downloads_per_hour = max_per_hour
        if min_delay is not None:
            self.min_delay_seconds = min_delay
        if max_delay is not None:
            self.max_delay_seconds = max_delay
