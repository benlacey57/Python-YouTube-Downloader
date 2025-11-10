"""Statistics management and alerts"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from rich.console import Console

from models.daily_stats import DailyStats
from models.download_alert import DownloadAlert
from managers.database_manager import DatabaseManager

console = Console()


class StatsManager:
    """Manages daily statistics and download alerts"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._initialize_alerts()

    def _initialize_alerts(self):
        """Initialize alert thresholds if they don't exist"""
        default_thresholds = [
            250 * 1024 * 1024,    # 250 MB
            1024 * 1024 * 1024,   # 1 GB
            5 * 1024 * 1024 * 1024,   # 5 GB
            10 * 1024 * 1024 * 1024,  # 10 GB
        ]
        
        for threshold in default_thresholds:
            existing = self.db.fetch_one(
                "SELECT * FROM download_alerts WHERE threshold_bytes = ?",
                (threshold,)
            )
            if not existing:
                alert = DownloadAlert(
                    id=None,
                    threshold_bytes=threshold
                )
                self.db.execute_query(
                    """INSERT INTO download_alerts 
                       (threshold_bytes, last_alert_date, total_size_at_alert)
                       VALUES (?, ?, ?)""",
                    alert.prepare_for_insert()
                )

    def get_today_stats(self) -> DailyStats:
        """Get or create today's statistics"""
        today = date.today().isoformat()
        
        row = self.db.fetch_one(
            "SELECT * FROM daily_stats WHERE date = ?",
            (today,)
        )
        
        if row:
            return DailyStats.from_row(tuple(row))
        else:
            stats = DailyStats(
                id=None,
                date=today
            )
            self.db.execute_query(
                """INSERT INTO daily_stats 
                   (date, videos_downloaded, videos_queued, videos_failed,
                    total_download_time_seconds, total_file_size_bytes,
                    queues_created, queues_completed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                stats.prepare_for_insert()
            )
            # Fetch it back to get the ID
            row = self.db.fetch_one(
                "SELECT * FROM daily_stats WHERE date = ?",
                (today,)
            )
            return DailyStats.from_row(tuple(row))

    def record_download(self, success: bool, duration_seconds: float, file_size_bytes: int = 0):
        """Record a completed download"""
        stats = self.get_today_stats()
        
        if success:
            stats.videos_downloaded += 1
            stats.total_download_time_seconds += duration_seconds
            stats.total_file_size_bytes += file_size_bytes
        else:
            stats.videos_failed += 1
        
        self.db.execute_query(
            """UPDATE daily_stats SET 
               videos_downloaded = ?, videos_queued = ?, videos_failed = ?,
               total_download_time_seconds = ?, total_file_size_bytes = ?,
               queues_created = ?, queues_completed = ?
               WHERE date = ?""",
            stats.prepare_for_update()
        )

    def record_queue_created(self, num_items: int):
        """Record a new queue creation"""
        stats = self.get_today_stats()
        stats.queues_created += 1
        stats.videos_queued += num_items
        
        self.db.execute_query(
            """UPDATE daily_stats SET 
               videos_downloaded = ?, videos_queued = ?, videos_failed = ?,
               total_download_time_seconds = ?, total_file_size_bytes = ?,
               queues_created = ?, queues_completed = ?
               WHERE date = ?""",
            stats.prepare_for_update()
        )

    def record_queue_completed(self):
        """Record a queue completion"""
        stats = self.get_today_stats()
        stats.queues_completed += 1
        
        self.db.execute_query(
            """UPDATE daily_stats SET 
               videos_downloaded = ?, videos_queued = ?, videos_failed = ?,
               total_download_time_seconds = ?, total_file_size_bytes = ?,
               queues_created = ?, queues_completed = ?
               WHERE date = ?""",
            stats.prepare_for_update()
        )

    def check_alert_threshold(self, file_size_bytes: int) -> List[int]:
        """Check if download size crossed any alert thresholds"""
        stats = self.get_today_stats()
        triggered_thresholds = []
        
        rows = self.db.fetch_all(
            "SELECT * FROM download_alerts ORDER BY threshold_bytes ASC"
        )
        
        for row in rows:
            alert = DownloadAlert.from_row(tuple(row))
            
            # Check if we crossed this threshold
            previous_size = stats.total_file_size_bytes - file_size_bytes
            current_size = stats.total_file_size_bytes
            
            # If we crossed the threshold today
            if previous_size < alert.threshold_bytes <= current_size:
                # Check if we already alerted today
                if alert.last_alert_date != date.today().isoformat():
                    triggered_thresholds.append(alert.threshold_bytes)
                    
                    # Update alert
                    alert.last_alert_date = date.today().isoformat()
                    alert.total_size_at_alert = current_size
                    
                    self.db.execute_query(
                        """UPDATE download_alerts SET 
                           last_alert_date = ?, total_size_at_alert = ?
                           WHERE threshold_bytes = ?""",
                        alert.prepare_for_update()
                    )
        
        return triggered_thresholds

    def get_date_range_stats(self, days: int = 30) -> List[DailyStats]:
        """Get statistics for the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        rows = self.db.fetch_all(
            """SELECT * FROM daily_stats 
               WHERE date >= ? AND date <= ?
               ORDER BY date ASC""",
            (start_date.isoformat(), end_date.isoformat())
        )
        
        # Create a dict of existing stats
        stats_dict = {
            DailyStats.from_row(tuple(row)).date: DailyStats.from_row(tuple(row))
            for row in rows
        }
        
        # Fill in missing dates with zero stats
        stats_list = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in stats_dict:
                stats_list.append(stats_dict[date_str])
            else:
                stats_list.append(DailyStats(id=None, date=date_str))
            current_date += timedelta(days=1)
        
        return stats_list

    def get_summary(self, days: int = 30) -> Dict:
        """Get summary statistics for the last N days"""
        stats_list = self.get_date_range_stats(days)

        return {
            'total_downloaded': sum(s.videos_downloaded for s in stats_list),
            'total_queued': sum(s.videos_queued for s in stats_list),
            'total_failed': sum(s.videos_failed for s in stats_list),
            'total_time_seconds': sum(s.total_download_time_seconds for s in stats_list),
            'total_size_bytes': sum(s.total_file_size_bytes for s in stats_list),
            'avg_downloads_per_day': sum(s.videos_downloaded for s in stats_list) / days if days > 0 else 0,
            'queues_created': sum(s.queues_created for s in stats_list),
            'queues_completed': sum(s.queues_completed for s in stats_list),
          }
