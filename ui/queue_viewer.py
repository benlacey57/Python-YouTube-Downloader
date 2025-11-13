"""Queue viewer"""
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

from managers.queue_manager import QueueManager
from downloaders.playlist import PlaylistDownloader
from enums import DownloadStatus

console = Console()


class QueueViewer:
    """View and manage download queues"""
    
    def __init__(self):
        self.queue_manager = QueueManager()
        self.downloader = PlaylistDownloader()
    
    def show(self):
        """Show queue viewer"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Download Queues[/bold cyan]\n"
                "View and manage queues",
                border_style="cyan"
            )
            console.print(header)
            
            # Get all queues
            queues = self.queue_manager.get_all_queues()
            
            if not queues:
                console.print("\n[yellow]No queues found[/yellow]")
                input("\nPress Enter to continue...")
                return
            
            # Display queues
            table = Table(title="All Queues", show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Title", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Items", justify="right")
            table.add_column("Format", justify="center")
            table.add_column("Quality", justify="center")
            
            for idx, queue in enumerate(queues, 1):
                items = self.queue_manager.get_queue_items(queue.id)
                completed = sum(1 for i in items if i.status == DownloadStatus.COMPLETED.value)
                
                status_color = {
                    'pending': 'yellow',
                    'completed': 'green',
                    'failed': 'red'
                }.get(queue.status, 'white')
                
                table.add_row(
                    str(idx),
                    queue.playlist_title,
                    f"[{status_color}]{queue.status}[/{status_color}]",
                    f"{completed}/{len(items)}",
                    queue.format_type,
                    queue.quality
                )
            
            console.print("\n")
            console.print(table)
            
            console.print("\n[cyan]Options:[/cyan]")
            console.print("  1. View queue details")
            console.print("  2. Download queue")
            console.print("  3. Delete queue")
            console.print("  4. Back to main menu")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4"],
                default="4"
            )
            
            if choice == "1":
                self._view_queue_details(queues)
            elif choice == "2":
                self._download_queue(queues)
            elif choice == "3":
                self._delete_queue(queues)
            elif choice == "4":
                break
    
    def _view_queue_details(self, queues):
        """View detailed queue information"""
        queue_num = IntPrompt.ask(
            "\nSelect queue number",
            choices=[str(i) for i in range(1, len(queues) + 1)]
        )
        
        queue = queues[queue_num - 1]
        items = self.queue_manager.get_queue_items(queue.id)
        
        console.clear()
        
        # Queue info
        info_table = Table(title=f"Queue: {queue.playlist_title}", show_header=False)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        info_table.add_row("Status", queue.status)
        info_table.add_row("Format", queue.format_type)
        info_table.add_row("Quality", queue.quality)
        info_table.add_row("Output", queue.output_dir)
        info_table.add_row("Created", queue.created_at)
        
        if queue.completed_at:
            info_table.add_row("Completed", queue.completed_at)
        
        console.print(info_table)
        
        # Items
        console.print("\n[cyan]Download Items:[/cyan]")
        
        items_table = Table(show_header=True)
        items_table.add_column("#", style="cyan", width=4)
        items_table.add_column("Title", style="green")
        items_table.add_column("Status", style="yellow")
        items_table.add_column("Size", justify="right")
        
        for idx, item in enumerate(items, 1):
            status_color = {
                'pending': 'yellow',
                'downloading': 'blue',
                'completed': 'green',
                'failed': 'red'
            }.get(item.status, 'white')
            
            size_str = ""
            if item.file_size_bytes:
                size_mb = item.file_size_bytes / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            
            items_table.add_row(
                str(idx),
                item.title[:50],
                f"[{status_color}]{item.status}[/{status_color}]",
                size_str
            )
        
        console.print(items_table)
        
        # Statistics
        stats = self.queue_manager.get_queue_stats(queue.id)
        
        console.print("\n[cyan]Statistics:[/cyan]")
        console.print(f"  Total items: {stats['total']}")
        console.print(f"  Completed: {stats['completed']}")
        console.print(f"  Failed: {stats['failed']}")
        console.print(f"  Pending: {stats['pending']}")
        console.print(f"  Total size: {stats['total_size_mb']:.1f} MB")
        
        input("\nPress Enter to continue...")
    
    def _download_queue(self, queues):
        """Download a queue"""
        pending = [q for q in queues if q.status == 'pending']
        
        if not pending:
            console.print("\n[yellow]No pending queues[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Pending Queues:[/cyan]")
        for idx, queue in enumerate(pending, 1):
            console.print(f"  {idx}. {queue.playlist_title}")
        
        queue_num = IntPrompt.ask(
            "\nSelect queue number",
            choices=[str(i) for i in range(1, len(pending) + 1)]
        )
        
        queue = pending[queue_num - 1]
        self.downloader.download_queue(queue, self.queue_manager)
    
    def _delete_queue(self, queues):
        """Delete a queue"""
        queue_num = IntPrompt.ask(
            "\nSelect queue number to delete",
            choices=[str(i) for i in range(1, len(queues) + 1)]
        )
        
        queue = queues[queue_num - 1]
        
        if Confirm.ask(f"\n[red]Delete queue '{queue.playlist_title}'?[/red]", default=False):
            self.queue_manager.delete_queue(queue.id)
            console.print("\n[green]✓ Queue deleted[/green]")
            input("\nPress Enter to continue...")
