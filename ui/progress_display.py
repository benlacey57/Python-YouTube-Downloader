"""Custom progress display for downloads"""
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.console import Console


class ProgressDisplay:
    """Handles clean progress display for downloads"""

    def __init__(self):
        self.console = Console()
        self.progress = None
        self.task_id = None

    def create_simple_progress(self, description: str, total: int = 100):
        """Create a simple progress bar"""
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        self.progress.start()
        self.task_id = self.progress.add_task(description, total=total)

    def update_progress(self, completed: int):
        """Update progress"""
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, completed=completed)

    def complete_progress(self):
        """Mark progress as complete"""
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.task_id = None

    def get_yt_dlp_progress_hook(self):
        """Get a progress hook for yt-dlp"""
        def hook(d):
            if d['status'] == 'downloading':
                if self.progress and self.task_id is not None:
                    try:
                        # Extract progress information
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        
                        if total > 0:
                            percentage = (downloaded / total) * 100
                            self.progress.update(self.task_id, completed=percentage)
                    except Exception:
                        pass
            elif d['status'] == 'finished':
                if self.progress and self.task_id is not None:
                    self.progress.update(self.task_id, completed=100)

        return hook
