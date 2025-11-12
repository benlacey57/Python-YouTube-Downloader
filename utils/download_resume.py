"""Download resume functionality"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from rich.console import Console

console = Console()


class DownloadResume:
    """Manages resume information for partial downloads"""
    
    def __init__(self, resume_file: str = "data/resume_info.json"):
        self.resume_file = Path(resume_file)
        self.resume_file.parent.mkdir(parents=True, exist_ok=True)
        self.resume_data = self._load_resume_data()
    
    def _load_resume_data(self) -> Dict[str, Any]:
        """Load resume data from file"""
        if self.resume_file.exists():
            try:
                with open(self.resume_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load resume data: {e}[/yellow]")
                return {}
        return {}
    
    def _save_resume_data(self):
        """Save resume data to file"""
        try:
            with open(self.resume_file, 'w') as f:
                json.dump(self.resume_data, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save resume data: {e}[/yellow]")
    
    def record_partial_download(self, video_id: str, url: str, 
                               partial_path: str, size_bytes: int):
        """Record information about a partial download"""
        if not video_id:
            return
        
        self.resume_data[video_id] = {
            'url': url,
            'partial_path': partial_path,
            'size_bytes': size_bytes,
            'timestamp': datetime.now().isoformat(),
            'attempts': self.resume_data.get(video_id, {}).get('attempts', 0) + 1
        }
        
        self._save_resume_data()
        console.print(f"[yellow]Recorded partial download: {video_id} ({size_bytes} bytes)[/yellow]")
    
    def get_resume_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get resume information for a video"""
        return self.resume_data.get(video_id)
    
    def can_resume(self, video_id: str, max_attempts: int = 3) -> bool:
        """Check if a download can be resumed"""
        info = self.get_resume_info(video_id)
        if not info:
            return False
        
        # Check if partial file still exists
        partial_path = Path(info['partial_path'])
        if not partial_path.exists():
            self.clear_resume_info(video_id)
            return False
        
        # Check if too many attempts
        if info.get('attempts', 0) >= max_attempts:
            console.print(f"[yellow]Max resume attempts reached for {video_id}[/yellow]")
            return False
        
        return True
    
    def clear_resume_info(self, video_id: str):
        """Clear resume information for a video"""
        if video_id in self.resume_data:
            # Try to delete partial file
            info = self.resume_data[video_id]
            partial_path = Path(info['partial_path'])
            if partial_path.exists():
                try:
                    partial_path.unlink()
                    console.print(f"[dim]Deleted partial file: {partial_path}[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Could not delete partial file: {e}[/yellow]")
            
            del self.resume_data[video_id]
            self._save_resume_data()
    
    def clear_all_resume_info(self):
        """Clear all resume information"""
        # Delete all partial files
        for video_id, info in self.resume_data.items():
            partial_path = Path(info['partial_path'])
            if partial_path.exists():
                try:
                    partial_path.unlink()
                except Exception as e:
                    console.print(f"[yellow]Could not delete {partial_path}: {e}[/yellow]")
        
        self.resume_data = {}
        self._save_resume_data()
        console.print("[green]✓ Cleared all resume information[/green]")
    
    def get_all_partial_downloads(self) -> Dict[str, Any]:
        """Get all partial download information"""
        return self.resume_data.copy()
    
    def cleanup_old_partials(self, max_age_days: int = 7):
        """Remove resume info older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        to_remove = []
        
        for video_id, info in self.resume_data.items():
            try:
                timestamp = datetime.fromisoformat(info['timestamp'])
                if timestamp < cutoff_date:
                    to_remove.append(video_id)
            except:
                to_remove.append(video_id)  # Remove invalid entries
        
        for video_id in to_remove:
            console.print(f"[dim]Removing old partial download: {video_id}[/dim]")
            self.clear_resume_info(video_id)
        
        if to_remove:
            console.print(f"[green]✓ Cleaned up {len(to_remove)} old partial downloads[/green]")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about partial downloads"""
        total_size = sum(info['size_bytes'] for info in self.resume_data.values())
        total_count = len(self.resume_data)
        
        # Count by attempts
        attempts_breakdown = {}
        for info in self.resume_data.values():
            attempts = info.get('attempts', 1)
            attempts_breakdown[attempts] = attempts_breakdown.get(attempts, 0) + 1
        
        return {
            'total_partials': total_count,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'attempts_breakdown': attempts_breakdown
        }
    
    def display_partial_downloads(self):
        """Display information about partial downloads"""
        from rich.table import Table
        
        if not self.resume_data:
            console.print("[yellow]No partial downloads found[/yellow]")
            return
        
        table = Table(title="Partial Downloads", show_header=True)
        table.add_column("Video ID", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Attempts", justify="center")
        table.add_column("Date", style="dim")
        
        for video_id, info in self.resume_data.items():
            size_mb = info['size_bytes'] / (1024 * 1024)
            timestamp = datetime.fromisoformat(info['timestamp'])
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            
            table.add_row(
                video_id[:12] + "...",
                f"{size_mb:.1f} MB",
                str(info.get('attempts', 1)),
                date_str
            )
        
        console.print(table)
        
        # Show stats
        stats = self.get_stats()
        console.print(f"\n[cyan]Total: {stats['total_partials']} partial downloads ({stats['total_size_mb']:.1f} MB)[/cyan]")
