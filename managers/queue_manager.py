"""Queue management"""
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
from rich.console import Console

from models.queue import Queue
from models.download_item import DownloadItem
from managers.database_manager import DatabaseManager
from managers.stats_manager import StatsManager
from enums import DownloadStatus

console = Console()


class QueueManager:
    """Manages download queues and items"""

    def __init__(self, db_manager: DatabaseManager, stats_manager: Optional[StatsManager] = None):
        self.db = db_manager
        self.stats_manager = stats_manager

    def create_queue(self, channel_id: Optional[int], playlist_url: str, 
                     playlist_title: str, format_type: str, quality: str,
                     output_dir: str, items: List[Dict], download_order: str = "original",
                     filename_template: Optional[str] = None) -> str:
        """Create a new download queue"""
        queue_id = hashlib.md5(
            f"{playlist_url}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        queue = Queue(
            id=queue_id,
            channel_id=channel_id,
            playlist_url=playlist_url,
            playlist_title=playlist_title,
            format_type=format_type,
            quality=quality,
            output_dir=output_dir,
            download_order=download_order,
            filename_template=filename_template,
            is_monitored=False,
            created_at=datetime.now().isoformat()
        )

        # Insert queue
        self.db.execute_query(
            """INSERT INTO queues 
               (id, channel_id, playlist_url, playlist_title, format_type,
                quality, output_dir, download_order, filename_template,
                is_monitored, created_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            queue.prepare_for_insert()
        )

        # Insert items
        for item_data in items:
            item = DownloadItem(
                id=None,
                queue_id=queue_id,
                url=item_data['url'],
                title=item_data['title'],
                status=DownloadStatus.PENDING.value,
                upload_date=item_data.get('upload_date'),
                uploader=item_data.get('uploader'),
                video_id=item_data.get('video_id')
            )
            
            self.db.execute_query(
                """INSERT INTO download_items 
                   (queue_id, url, title, status, file_path, error, file_hash,
                    download_started_at, download_completed_at, download_duration_seconds,
                    upload_date, uploader, video_id, file_size_bytes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                item.prepare_for_insert()
            )

        # Record stats
        if self.stats_manager:
            self.stats_manager.record_queue_created(len(items))

        return queue_id

    def get_queue(self, queue_id: str) -> Optional[Queue]:
        """Get a queue by ID"""
        row = self.db.fetch_one(
            "SELECT * FROM queues WHERE id = ?",
            (queue_id,)
        )
        
        if row:
            return Queue.from_row(tuple(row))
        return None

    def get_queue_items(self, queue_id: str) -> List[DownloadItem]:
        """Get all items for a queue"""
        rows = self.db.fetch_all(
            "SELECT * FROM download_items WHERE queue_id = ? ORDER BY id ASC",
            (queue_id,)
        )
        
        return [DownloadItem.from_row(tuple(row)) for row in rows]

    def update_queue(self, queue: Queue):
        """Update a queue"""
        self.db.execute_query(
            "UPDATE queues SET completed_at = ? WHERE id = ?",
            queue.prepare_for_update()
        )

    def update_item(self, item: DownloadItem):
        """Update a download item"""
        self.db.execute_query(
            """UPDATE download_items SET 
               status = ?, file_path = ?, error = ?, file_hash = ?,
               download_started_at = ?, download_completed_at = ?,
               download_duration_seconds = ?, file_size_bytes = ?
               WHERE id = ?""",
            item.prepare_for_update()
        )

    def list_incomplete_queues(self) -> List[Queue]:
        """Get all incomplete queues"""
        rows = self.db.fetch_all(
            """SELECT DISTINCT q.* FROM queues q
               INNER JOIN download_items di ON q.id = di.queue_id
               WHERE di.status IN (?, ?)""",
            (DownloadStatus.PENDING.value, DownloadStatus.FAILED.value)
        )
        
        return [Queue.from_row(tuple(row)) for row in rows]

    def get_statistics(self) -> Dict:
        """Get overall queue statistics"""
        queue_count = self.db.fetch_one("SELECT COUNT(*) FROM queues")
        item_count = self.db.fetch_one("SELECT COUNT(*) FROM download_items")
        completed_count = self.db.fetch_one(
            "SELECT COUNT(*) FROM download_items WHERE status = ?",
            (DownloadStatus.COMPLETED.value,)
        )
        failed_count = self.db.fetch_one(
            "SELECT COUNT(*) FROM download_items WHERE status = ?",
            (DownloadStatus.FAILED.value,)
        )
        
        total_time = self.db.fetch_one(
            "SELECT SUM(download_duration_seconds) FROM download_items"
        )
        
        return {
            'total_queues': queue_count[0] if queue_count else 0,
            'total_items': item_count[0] if item_count else 0,
            'completed_items': completed_count[0] if completed_count else 0,
            'failed_items': failed_count[0] if failed_count else 0,
            'pending_items': (item_count[0] if item_count else 0) - 
                           (completed_count[0] if completed_count else 0) - 
                           (failed_count[0] if failed_count else 0),
            'total_time': total_time[0] if total_time and total_time[0] else 0
        }
