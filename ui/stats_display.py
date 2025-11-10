"""Statistics display"""
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel

console = Console()


class StatsDisplay:
    """Handles statistics display"""

    @staticmethod
    def display_statistics(stats_manager, queue_manager):
        """Display detailed statistics"""
        console.print("\n")

        summary_7 = stats_manager.get_summary(7)
        summary_30 = stats_manager.get_summary(30)

        # Summary table
        table = Table(title="Statistics Summary", show_header=True, header_style="bold cyan")
        table.add_column("Period", style="cyan")
        table.add_column("Downloaded", style="green", justify="right")
        table.add_column("Queued", style="yellow", justify="right")
        table.add_column("Failed", style="red", justify="right")
        table.add_column("Avg/Day", style="blue", justify="right")
        table.add_column("Total Size", style="magenta")

        table.add_row(
            "Last 7 Days",
            str(summary_7['total_downloaded']),
            str(summary_7['total_queued']),
            str(summary_7['total_failed']),
            f"{summary_7['avg_downloads_per_day']:.1f}",
            StatsDisplay._format_size(summary_7['total_size_bytes'])
        )

        table.add_row(
            "Last 30 Days",
            str(summary_30['total_downloaded']),
            str(summary_30['total_queued']),
            str(summary_30['total_failed']),
            f"{summary_30['avg_downloads_per_day']:.1f}",
            StatsDisplay._format_size(summary_30['total_size_bytes'])
        )

        console.print(table)

        # Daily breakdown
        console.print("\n")
        daily_stats = stats_manager.get_date_range_stats(14)

        daily_table = Table(title="Last 14 Days", show_header=True, header_style="bold cyan")
        daily_table.add_column("Date", style="cyan")
        daily_table.add_column("Downloaded", style="green", justify="right")
        daily_table.add_column("Failed", style="red", justify="right")
        daily_table.add_column("Time", style="blue")
        daily_table.add_column("Size", style="magenta")

        for stat in reversed(daily_stats):
            if stat.videos_downloaded > 0 or stat.videos_failed > 0:
                daily_table.add_row(
                    stat.date,
                    str(stat.videos_downloaded),
                    str(stat.videos_failed),
                    StatsDisplay._format_duration(stat.total_download_time_seconds),
                    StatsDisplay._format_size(stat.total_file_size_bytes)
                )

        console.print(daily_table)

    @staticmethod
    def display_dashboard(queue_manager, monitor_manager, stats_manager):
        """Create dashboard layout with statistics"""
        layout = Layout()

        stats = queue_manager.get_statistics()
        daily_summary = stats_manager.get_summary(7)

        # Queue statistics panel
        stats_content = (
            f"[cyan]Total Queues:[/cyan] {stats['total_queues']}\n"
            f"[green]Completed:[/green] {stats['completed_items']}\n"
            f"[yellow]Pending:[/yellow] {stats['pending_items']}\n"
            f"[red]Failed:[/red] {stats['failed_items']}\n"
            f"[blue]Total Time:[/blue] {StatsDisplay._format_duration(stats['total_time'])}"
        )

        stats_panel = Panel(
            stats_content,
            title="[bold]Queue Statistics[/bold]",
            border_style="cyan"
        )

        # Daily statistics panel
        daily_content = (
            f"[cyan]Last 7 Days:[/cyan]\n"
            f"[green]Downloaded:[/green] {daily_summary['total_downloaded']}\n"
            f"[yellow]Queued:[/yellow] {daily_summary['total_queued']}\n"
            f"[red]Failed:[/red] {daily_summary['total_failed']}\n"
            f"[blue]Avg/Day:[/blue] {daily_summary['avg_downloads_per_day']:.1f}\n"
            f"[magenta]Size:[/magenta] {StatsDisplay._format_size(daily_summary['total_size_bytes'])}"
        )

        daily_panel = Panel(
            daily_content,
            title="[bold]Daily Statistics[/bold]",
            border_style="green"
        )

        # Monitoring status panel
        channels = monitor_manager.get_all_channels()
        monitored_count = len([c for c in channels if c.is_monitored])
        monitor_status = "Running" if monitor_manager.is_running else "Stopped"
        monitor_color = "green" if monitor_manager.is_running else "red"

        monitor_content = (
            f"[{monitor_color}]Status:[/{monitor_color}] {monitor_status}\n"
            f"[cyan]Monitored Channels:[/cyan] {monitored_count}"
        )

        monitor_panel = Panel(
            monitor_content,
            title="[bold]Monitoring[/bold]",
            border_style=monitor_color
        )

        layout.split_row(
            Layout(stats_panel),
            Layout(daily_panel),
            Layout(monitor_panel)
        )

        return layout

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds is None or seconds == 0:
            return "N/A"

        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """Format file size in human-readable format"""
        if bytes_size is None or bytes_size == 0:
            return "N/A"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
