"""Statistics viewer"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from datetime import datetime, timedelta

from managers.stats_manager import StatsManager

console = Console()


class StatsViewer:
    """View download statistics"""
    
    def __init__(self):
        self.stats_manager = StatsManager()
    
    def show(self):
        """Show statistics viewer"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Download Statistics[/bold cyan]\n"
                "View detailed statistics",
                border_style="cyan"
            )
            console.print(header)
            
            console.print("\n[cyan]Options:[/cyan]")
            console.print("  1. Today's statistics")
            console.print("  2. Weekly statistics")
            console.print("  3. All-time statistics")
            console.print("  4. Date range statistics")
            console.print("  5. Back to main menu")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5"],
                default="5"
            )
            
            if choice == "1":
                self._show_today_stats()
            elif choice == "2":
                self._show_weekly_stats()
            elif choice == "3":
                self._show_all_time_stats()
            elif choice == "4":
                self._show_date_range_stats()
            elif choice == "5":
                break
    
    def _show_today_stats(self):
        """Show today's statistics"""
        console.clear()
        console.print(Panel("[bold cyan]Today's Statistics[/bold cyan]", border_style="cyan"))
        
        stats = self.stats_manager.get_today_stats()
        
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Total Downloads", str(stats.total_downloads))
        table.add_row("Successful", str(stats.successful_downloads))
        table.add_row("Failed", str(stats.failed_downloads))
        
        success_rate = (
            (stats.successful_downloads / stats.total_downloads * 100)
            if stats.total_downloads > 0 else 0
        )
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        table.add_row("Queues Completed", str(stats.queues_completed))
        table.add_row(
            "Data Downloaded",
            f"{stats.total_file_size_bytes / (1024**3):.2f} GB"
        )
        
        console.print("\n")
        console.print(table)
        
        input("\nPress Enter to continue...")
    
    def _show_weekly_stats(self):
        """Show weekly statistics"""
        console.clear()
        console.print(Panel("[bold cyan]Weekly Statistics[/bold cyan]", border_style="cyan"))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats_list = self.stats_manager.get_date_range_stats(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if not stats_list:
            console.print("\n[yellow]No statistics available for this period[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        # Daily breakdown
        table = Table(title="Daily Breakdown", show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Downloads", justify="right")
        table.add_column("Successful", justify="right")
        table.add_column("Size (GB)", justify="right")
        
        total_downloads = 0
        total_successful = 0
        total_size = 0
        
        for stat in stats_list:
            total_downloads += stat.total_downloads
            total_successful += stat.successful_downloads
            total_size += stat.total_file_size_bytes
            
            table.add_row(
                stat.date,
                str(stat.total_downloads),
                str(stat.successful_downloads),
                f"{stat.total_file_size_bytes / (1024**3):.2f}"
            )
        
        console.print("\n")
        console.print(table)
        
        # Summary
        console.print("\n[cyan]Week Summary:[/cyan]")
        console.print(f"  Total Downloads: {total_downloads}")
        console.print(f"  Successful: {total_successful}")
        console.print(f"  Total Size: {total_size / (1024**3):.2f} GB")
        
        input("\nPress Enter to continue...")
    
    def _show_all_time_stats(self):
        """Show all-time statistics"""
        console.clear()
        console.print(Panel("[bold cyan]All-Time Statistics[/bold cyan]", border_style="cyan"))
        
        all_stats = self.stats_manager.get_all_stats()
        
        if not all_stats:
            console.print("\n[yellow]No statistics available[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        total_downloads = sum(s.total_downloads for s in all_stats)
        total_successful = sum(s.successful_downloads for s in all_stats)
        total_failed = sum(s.failed_downloads for s in all_stats)
        total_size = sum(s.total_file_size_bytes for s in all_stats)
        total_queues = sum(s.queues_completed for s in all_stats)
        
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Total Downloads", str(total_downloads))
        table.add_row("Successful", str(total_successful))
        table.add_row("Failed", str(total_failed))
        
        success_rate = (
            (total_successful / total_downloads * 100)
            if total_downloads > 0 else 0
        )
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        table.add_row("Queues Completed", str(total_queues))
        table.add_row("Total Data Downloaded", f"{total_size / (1024**3):.2f} GB")
        table.add_row("Days Active", str(len(all_stats)))
        
        if total_downloads > 0:
            avg_per_day = total_downloads / len(all_stats)
            table.add_row("Avg Downloads/Day", f"{avg_per_day:.1f}")
        
        console.print("\n")
        console.print(table)
        
        input("\nPress Enter to continue...")
    
    def _show_date_range_stats(self):
        """Show statistics for custom date range"""
        console.clear()
        console.print(Panel("[bold cyan]Date Range Statistics[/bold cyan]", border_style="cyan"))
        
        start_date = Prompt.ask("\nStart date (YYYY-MM-DD)")
        end_date = Prompt.ask("End date (YYYY-MM-DD)")
        
        try:
            # Validate dates
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            console.print("\n[red]Invalid date format[/red]")
            input("\nPress Enter to continue...")
            return
        
        stats_list = self.stats_manager.get_date_range_stats(start_date, end_date)
        
        if not stats_list:
            console.print("\n[yellow]No statistics available for this period[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        # Daily breakdown
        table = Table(title=f"Statistics: {start_date} to {end_date}", show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Downloads", justify="right")
        table.add_column("Successful", justify="right")
        table.add_column("Size (GB)", justify="right")
        
        total_downloads = 0
        total_successful = 0
        total_size = 0
        
        for stat in stats_list:
            total_downloads += stat.total_downloads
            total_successful += stat.successful_downloads
            total_size += stat.total_file_size_bytes
            
            table.add_row(
                stat.date,
                str(stat.total_downloads),
                str(stat.successful_downloads),
                f"{stat.total_file_size_bytes / (1024**3):.2f}"
            )
        
        console.print("\n")
        console.print(table)
        
        # Summary
        console.print("\n[cyan]Period Summary:[/cyan]")
        console.print(f"  Total Downloads: {total_downloads}")
        console.print(f"  Successful: {total_successful}")
        console.print(f"  Total Size: {total_size / (1024**3):.2f} GB")
        
        input("\nPress Enter to continue...")
