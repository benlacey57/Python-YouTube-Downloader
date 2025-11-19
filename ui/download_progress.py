"""Enhanced download progress display"""
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.live import Live
from rich.table import Table
from rich.text import Text
from typing import Dict, List
from datetime import datetime

console = Console()


class DownloadProgressDisplay:
    """Enhanced progress display for downloads with overall stats"""
    
    def __init__(self, total_items: int):
        self.total_items = total_items
        self.completed = 0
        self.failed = 0
        self.downloading = 0
        self.items: Dict[int, Dict] = {}  # item_id -> {title, status, index}
        self.current_item_index = 0
        self.live = None
        self.progress = None
        self.task_id = None
    
    def start(self):
        """Start the live display"""
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        self.task_id = self.progress.add_task("", total=100)
        self.live = Live(self._build_display(), console=console, refresh_per_second=4)
        self.live.start()
    
    def stop(self):
        """Stop the live display"""
        if self.live:
            self.live.stop()
    
    def add_item(self, item_id: int, title: str, index: int):
        """Add a new item to track"""
        self.items[item_id] = {
            'title': title,
            'status': 'pending',
            'index': index
        }
    
    def update_item_status(self, item_id: int, status: str):
        """Update item status: downloading, completed, failed"""
        if item_id in self.items:
            old_status = self.items[item_id]['status']
            self.items[item_id]['status'] = status
            
            # Update counters
            if old_status == 'downloading':
                self.downloading -= 1
            
            if status == 'downloading':
                self.downloading += 1
                self.current_item_index = self.items[item_id]['index']
            elif status == 'completed':
                self.completed += 1
            elif status == 'failed':
                self.failed += 1
            
            self._update_display()
    
    def update_progress(self, percentage: float, description: str = "Downloading"):
        """Update the progress bar"""
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, completed=percentage, description=description)
            self._update_display()
    
    def _build_display(self) -> Panel:
        """Build the display layout"""
        # Stats panel
        stats_table = Table.grid(padding=(0, 2))
        stats_table.add_column(style="cyan", justify="right")
        stats_table.add_column(style="white")
        
        stats_table.add_row("Total:", f"{self.total_items}")
        stats_table.add_row("Completed:", f"[green]{self.completed}[/green]")
        stats_table.add_row("Failed:", f"[red]{self.failed}[/red]")
        stats_table.add_row("In Progress:", f"[yellow]{self.downloading}[/yellow]")
        
        # Items list (show last 10 items)
        items_display = []
        sorted_items = sorted(self.items.items(), key=lambda x: x[1]['index'])
        
        # Show items around current position
        display_start = max(0, self.current_item_index - 5)
        display_end = min(len(sorted_items), self.current_item_index + 5)
        
        for item_id, data in sorted_items[display_start:display_end]:
            index = data['index']
            title = data['title']
            status = data['status']
            
            # Truncate title if too long
            max_title_len = 60
            if len(title) > max_title_len:
                title = title[:max_title_len - 3] + "..."
            
            # Format line
            status_text = ""
            if status == 'completed':
                status_text = "[green]Downloaded[/green]"
            elif status == 'failed':
                status_text = "[red]Error[/red]"
            elif status == 'downloading':
                status_text = "[yellow]Downloading[/yellow]"
            else:
                status_text = "[dim]Pending[/dim]"
            
            # Create line with dots padding
            line = f"{index:03d} - {title} "
            padding_len = max(0, 80 - len(line) - len(status))
            padding = "." * padding_len
            
            items_display.append(f"{line}[dim]{padding}[/dim] {status_text}")
        
        items_text = "\n".join(items_display) if items_display else "[dim]No items to display[/dim]"
        
        # Progress bar
        progress_panel = self.progress if self.progress else ""
        
        # Combine everything
        layout = f"""[bold cyan]Download Progress[/bold cyan]

{stats_table}

{items_text}

{progress_panel}"""
        
        return Panel(
            layout,
            title=f"[bold]Downloading Queue[/bold]",
            border_style="cyan"
        )
    
    def _update_display(self):
        """Update the live display"""
        if self.live:
            self.live.update(self._build_display())
