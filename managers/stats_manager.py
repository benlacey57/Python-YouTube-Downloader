"""Statistics management"""
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
from rich.console import Console

from models.daily_stats import DailyStats
from models.download_alert import DownloadAlert
from managers.database_manager import DatabaseManager

console = Console()

@dataclass
class DownloadStats:
    """Download statistics data"""
    date: str
    total_downloads: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    total_file_size_bytes: int = 0
    total_duration_seconds: float = 0.0
    queues_completed: int = 0


class StatsManager:
    """Manages download statistics"""
    
    def __init__(self, db_path: str = "stats.db"):
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        """Initialize statistics database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_downloads INTEGER DEFAULT 0,
                    successful_downloads INTEGER DEFAULT 0,
                    failed_downloads INTEGER DEFAULT 0,
                    total_file_size_bytes INTEGER DEFAULT 0,
                    total_duration_seconds REAL DEFAULT 0.0,
                    queues_completed INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    threshold_bytes INTEGER NOT NULL,
                    triggered_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def record_download(self, success: bool, duration_seconds: float, file_size_bytes: int):
        """Record a download attempt"""
        today = date.today().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get or create today's stats
            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (today,))
            row = cursor.fetchone()
            
            if row:
                # Update existing stats
                cursor.execute("""
                    UPDATE daily_stats 
                    SET total_downloads = total_downloads + 1,
                        successful_downloads = successful_downloads + ?,
                        failed_downloads = failed_downloads + ?,
                        total_file_size_bytes = total_file_size_bytes + ?,
                        total_duration_seconds = total_duration_seconds + ?
                    WHERE date = ?
                """, (
                    1 if success else 0,
                    0 if success else 1,
                    file_size_bytes,
                    duration_seconds,
                    today
                ))
            else:
                # Insert new stats
                cursor.execute("""
                    INSERT INTO daily_stats (
                        date, total_downloads, successful_downloads,
                        failed_downloads, total_file_size_bytes, total_duration_seconds
                    ) VALUES (?, 1, ?, ?, ?, ?)
                """, (
                    today,
                    1 if success else 0,
                    0 if success else 1,
                    file_size_bytes,
                    duration_seconds
                ))
            
            conn.commit()
    
    def record_queue_completed(self):
        """Record a completed queue"""
        today = date.today().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (today,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute("""
                    UPDATE daily_stats 
                    SET queues_completed = queues_completed + 1
                    WHERE date = ?
                """, (today,))
            else:
                cursor.execute("""
                    INSERT INTO daily_stats (date, queues_completed)
                    VALUES (?, 1)
                """, (today,))
            
            conn.commit()
    
    def get_today_stats(self) -> DownloadStats:
        """Get today's statistics"""
        today = date.today().isoformat()
        return self.get_stats_for_date(today)
    
    def get_stats_for_date(self, date_str: str) -> DownloadStats:
        """Get statistics for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date_str,))
            row = cursor.fetchone()
            
            if row:
                return DownloadStats(
                    date=row[0],
                    total_downloads=row[1],
                    successful_downloads=row[2],
                    failed_downloads=row[3],
                    total_file_size_bytes=row[4],
                    total_duration_seconds=row[5],
                    queues_completed=row[6]
                )
            else:
                return DownloadStats(date=date_str)
    
    def get_all_time_stats(self) -> DownloadStats:
        """Get all-time aggregate statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(total_downloads),
                    SUM(successful_downloads),
                    SUM(failed_downloads),
                    SUM(total_file_size_bytes),
                    SUM(total_duration_seconds),
                    SUM(queues_completed)
                FROM daily_stats
            """)
            row = cursor.fetchone()
            
            if row and row[0]:
                return DownloadStats(
                    date="all_time",
                    total_downloads=row[0] or 0,
                    successful_downloads=row[1] or 0,
                    failed_downloads=row[2] or 0,
                    total_file_size_bytes=row[3] or 0,
                    total_duration_seconds=row[4] or 0.0,
                    queues_completed=row[5] or 0
                )
            else:
                return DownloadStats(date="all_time")
    
    def get_date_range_stats(self, start_date: str, end_date: str) -> List[DownloadStats]:
        """Get statistics for a date range"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_stats 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
            
            return [
                DownloadStats(
                    date=row[0],
                    total_downloads=row[1],
                    successful_downloads=row[2],
                    failed_downloads=row[3],
                    total_file_size_bytes=row[4],
                    total_duration_seconds=row[5],
                    queues_completed=row[6]
                )
                for row in rows
            ]
    
    def check_alert_threshold(self, file_size_bytes: int) -> List[int]:
        """
        Check if any alert thresholds have been crossed
        Returns list of threshold bytes that were crossed
        """
        today = date.today().isoformat()
        stats = self.get_today_stats()
        
        # Common thresholds (in bytes)
        thresholds = [
            250 * 1024 * 1024,   # 250 MB
            1024 * 1024 * 1024,  # 1 GB
            5 * 1024 * 1024 * 1024,  # 5 GB
            10 * 1024 * 1024 * 1024  # 10 GB
        ]
        
        triggered = []
        previous_total = stats.total_file_size_bytes - file_size_bytes
        current_total = stats.total_file_size_bytes
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for threshold in thresholds:
                # Check if we crossed this threshold with this download
                if previous_total < threshold <= current_total:
                    # Check if we already alerted for this threshold today
                    cursor.execute("""
                        SELECT * FROM alert_history 
                        WHERE date = ? AND threshold_bytes = ?
                    """, (today, threshold))
                    
                    if not cursor.fetchone():
                        # Record the alert
                        cursor.execute("""
                            INSERT INTO alert_history (date, threshold_bytes, triggered_at)
                            VALUES (?, ?, ?)
                        """, (today, threshold, datetime.now().isoformat()))
                        
                        triggered.append(threshold)
            
            conn.commit()
        
        return triggered
    
    def get_alert_history(self, days: int = 7) -> List[tuple]:
        """Get alert history for the last N days"""
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, threshold_bytes, triggered_at
                FROM alert_history
                WHERE date BETWEEN ? AND ?
                ORDER BY triggered_at DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            return cursor.fetchall()
    
    def clear_stats(self, date_str: str = None):
        """Clear statistics (all or for specific date)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if date_str:
                cursor.execute("DELETE FROM daily_stats WHERE date = ?", (date_str,))
                cursor.execute("DELETE FROM alert_history WHERE date = ?", (date_str,))
            else:
                cursor.execute("DELETE FROM daily_stats")
                cursor.execute("DELETE FROM alert_history")
            
            conn.commit()
    
    def export_stats_to_csv(self, output_file: str):
        """Export statistics to CSV file"""
        import csv
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_stats 
                ORDER BY date DESC
            """)
            
            rows = cursor.fetchall()
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Date', 'Total Downloads', 'Successful', 'Failed',
                    'File Size (MB)', 'Duration (minutes)', 'Queues Completed'
                ])
                
                for row in rows:
                    size_mb = row[4] / (1024 * 1024) if row[4] else 0
                    duration_mins = row[5] / 60 if row[5] else 0
                    
                    writer.writerow([
                        row[0], row[1], row[2], row[3],
                        f"{size_mb:.2f}", f"{duration_mins:.2f}", row[6]
                    ])
                    
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
