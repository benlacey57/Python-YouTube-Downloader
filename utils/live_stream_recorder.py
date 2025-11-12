"""Live stream recording functionality"""
import yt_dlp
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()


class LiveStreamRecorder:
    """Handles live stream detection and recording"""
    
    def __init__(self):
        self.default_wait_minutes = 60
    
    def is_live_stream(self, info: dict) -> bool:
        """Check if the video is a live stream"""
        if not info:
            return False
        
        # Check various indicators of live streams
        is_live = info.get('is_live', False)
        was_live = info.get('was_live', False)
        live_status = info.get('live_status')
        
        # Check live status
        if live_status in ['is_live', 'is_upcoming', 'post_live']:
            return True
        
        # Check is_live flag
        if is_live:
            return True
        
        return False
    
    def is_upcoming_stream(self, info: dict) -> bool:
        """Check if stream is scheduled for future"""
        if not info:
            return False
        
        live_status = info.get('live_status')
        return live_status == 'is_upcoming'
    
    def get_stream_start_time(self, info: dict) -> Optional[str]:
        """Get scheduled start time for upcoming stream"""
        if not info:
            return None
        
        return info.get('release_timestamp') or info.get('timestamp')
    
    def get_recording_opts(self, wait_for_stream: bool = False, 
                          max_wait_minutes: int = 60) -> Dict[str, Any]:
        """Get yt-dlp options for recording live streams"""
        opts = {
            'format': 'best',
            'fragment_retries': 10,
            'retries': 10,
            'file_access_retries': 10,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
        }
        
        if wait_for_stream:
            opts['wait_for_video'] = (1, max_wait_minutes * 60)  # (min, max) seconds
            opts['live_from_start'] = True
        
        return opts
    
    def get_stream_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get information about a live stream"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not self.is_live_stream(info):
                    return None
                
                return {
                    'title': info.get('title'),
                    'uploader': info.get('uploader'),
                    'is_live': info.get('is_live', False),
                    'is_upcoming': self.is_upcoming_stream(info),
                    'start_time': self.get_stream_start_time(info),
                    'live_status': info.get('live_status'),
                    'url': url
                }
        
        except Exception as e:
            console.print(f"[red]Error getting stream info: {e}[/red]")
            return None
    
    def wait_for_stream_start(self, url: str, max_wait_minutes: int = 60) -> bool:
        """Wait for a scheduled stream to start"""
        console.print(f"[yellow]Waiting for stream to start (max {max_wait_minutes} minutes)...[/yellow]")
        
        import time
        check_interval = 60  # Check every minute
        elapsed = 0
        
        while elapsed < max_wait_minutes * 60:
            stream_info = self.get_stream_info(url)
            
            if stream_info and stream_info['is_live']:
                console.print("[green]✓ Stream has started![/green]")
                return True
            
            time.sleep(check_interval)
            elapsed += check_interval
            
            remaining = max_wait_minutes - (elapsed / 60)
            console.print(f"[dim]Still waiting... ({remaining:.0f} minutes remaining)[/dim]")
        
        console.print("[red]Stream did not start within wait period[/red]")
        return False
