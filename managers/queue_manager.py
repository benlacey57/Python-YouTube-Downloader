"""Queue manager with integrated resume functionality"""
import sqlite3
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import json

from models.queue import Queue
from models.download_item import DownloadItem
from enums import DownloadStatus


class QueueManager:
    """Manages download queues with resume support"""
    
    def __init__(self, db_path: str = "data/downloads.db"):
        self.db_path = db_path
        self.resume_file = Path("data/resume_info.json")
        self.resume_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.resume_data = self._load_resume_data()
    
    def _init_database(self):
        """Initialize database tables"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Queues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_url TEXT NOT NULL,
                    playlist_title TEXT NOT NULL,
                    format_type TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    output_dir TEXT NOT NULL,
                    filename_template TEXT,
                    download_order TEXT DEFAULT 'newest_first',
                    storage_provider TEXT DEFAULT 'local',
                    storage_video_quality TEXT,
                    storage_audio_quality TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            # Download items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    video_id TEXT,
                    uploader TEXT,
                    upload_date TEXT,
                    file_path TEXT,
                    file_size_bytes INTEGER,
                    file_hash TEXT,
                    status TEXT DEFAULT 'pending',
                    error TEXT,
                    download_started_at TEXT,
                    download_completed_at TEXT,
                    download_duration_seconds REAL,
                    FOREIGN KEY (queue_id) REFERENCES queues (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    # Resume functionality integrated into QueueManager
    
    def _load_resume_data(self) -> dict:
        """Load resume data from file"""
        if self.resume_file.exists():
            try:
                with open(self.resume_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_resume_data(self):
        """Save resume data to file"""
        try:
            with open(self.resume_file, 'w') as f:
                json.dump(self.resume_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save resume data: {e}")
    
    def record_queue_interruption(self, queue_id: int):
        """Record that a queue was interrupted"""
        queue = self.get_queue(queue_id)
        if not queue:
            return
        
        pending_items = [
            item for item in self.get_queue_items(queue_id)
            if item.status == DownloadStatus.PENDING.value
        ]
        
        self.resume_data[str(queue_id)] = {
            'queue_id': queue_id,
            'playlist_title': queue.playlist_title,
            'pending_count': len(pending_items),
            'timestamp': datetime.now().isoformat()
        }
        
        self._save_resume_data()
    
    def get_resumable_queues(self) -> List[dict]:
        """Get list of queues that can be resumed"""
        resumable = []
        
        for queue_id_str, info in self.resume_data.items():
            queue_id = int(queue_id_str)
            queue = self.get_queue(queue_id)
            
            if queue and info['pending_count'] > 0:
                resumable.append({
                    'queue_id': queue_id,
                    'playlist_title': info['playlist_title'],
                    'pending_count': info['pending_count'],
                    'timestamp': info['timestamp']
                })
        
        return resumable
    
    def clear_queue_resume(self, queue_id: int):
        """Clear resume data for a queue"""
        queue_id_str = str(queue_id)
        if queue_id_str in self.resume_data:
            del self.resume_data[queue_id_str]
            self._save_resume_data()
    
    def clear_all_resume_data(self):
        """Clear all resume data"""
        self.resume_data = {}
        self._save_resume_data()
    
    # Existing queue methods
    
    def create_queue(self, queue: Queue) -> int:
        """Create a new queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO queues (
                    playlist_url, playlist_title, format_type, quality,
                    output_dir, filename_template, download_order,
                    storage_provider, storage_video_quality, storage_audio_quality,
                    created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                queue.playlist_url,
                queue.playlist_title,
                queue.format_type,
                queue.quality,
                queue.output_dir,
                queue.filename_template,
                queue.download_order,
                queue.storage_provider,
                queue.storage_video_quality,
                queue.storage_audio_quality,
                queue.created_at,
                queue.status
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_queue(self, queue_id: int) -> Optional[Queue]:
        """Get queue by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM queues WHERE id = ?", (queue_id,))
            row = cursor.fetchone()
            
            if row:
                return Queue(
                    id=row['id'],
                    playlist_url=row['playlist_url'],
                    playlist_title=row['playlist_title'],
                    format_type=row['format_type'],
                    quality=row['quality'],
                    output_dir=row['output_dir'],
                    filename_template=row['filename_template'],
                    download_order=row['download_order'],
                    storage_provider=row['storage_provider'],
                    storage_video_quality=row['storage_video_quality'],
                    storage_audio_quality=row['storage_audio_quality'],
                    created_at=row['created_at'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    status=row['status']
                )
            return None
    
    def get_all_queues(self) -> List[Queue]:
        """Get all queues"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM queues ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            queues = []
            for row in rows:
                queues.append(Queue(
                    id=row['id'],
                    playlist_url=row['playlist_url'],
                    playlist_title=row['playlist_title'],
                    format_type=row['format_type'],
                    quality=row['quality'],
                    output_dir=row['output_dir'],
                    filename_template=row['filename_template'],
                    download_order=row['download_order'],
                    storage_provider=row['storage_provider'],
                    storage_video_quality=row['storage_video_quality'],
                    storage_audio_quality=row['storage_audio_quality'],
                    created_at=row['created_at'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    status=row['status']
                ))
            
            return queues
    
    def update_queue(self, queue: Queue):
    def update_queue(self, queue: Queue):
        """Update queue configuration and status fields"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE queues SET
                    playlist_url = ?,
                    playlist_title = ?,
                    format_type = ?,
                    quality = ?,
                    output_dir = ?,
                    filename_template = ?,
                    download_order = ?,
                    storage_provider = ?,
                    storage_video_quality = ?,
                    storage_audio_quality = ?,
                    started_at = ?,
                    completed_at = ?,
                    status = ?
                WHERE id = ?
            """, (
                queue.playlist_url,
                queue.playlist_title,
                queue.format_type,
                queue.quality,
                queue.output_dir,
                queue.filename_template,
                queue.download_order,
                queue.storage_provider,
                queue.storage_video_quality,
                queue.storage_audio_quality,
                queue.started_at,
                queue.completed_at,
                queue.status,
                queue.id
            ))
            conn.commit()
    
    def delete_queue(self, queue_id: int):
        """Delete queue and all its items"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM queues WHERE id = ?", (queue_id,))
            conn.commit()
        
        # Clear resume data
        self.clear_queue_resume(queue_id)
    
    def add_item(self, item: DownloadItem) -> int:
        """Add download item to queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO download_items (
                    queue_id, url, title, video_id, uploader, upload_date,
                    file_path, file_size_bytes, file_hash, status, error,
                    download_started_at, download_completed_at, download_duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.queue_id,
                item.url,
                item.title,
                item.video_id,
                item.uploader,
                item.upload_date,
                item.file_path,
                item.file_size_bytes,
                item.file_hash,
                item.status,
                item.error,
                item.download_started_at,
                item.download_completed_at,
                item.download_duration_seconds
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_queue_items(self, queue_id: int) -> List[DownloadItem]:
        """Get all items in queue"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM download_items 
                WHERE queue_id = ?
                ORDER BY id ASC
            """, (queue_id,))
            rows = cursor.fetchall()
            
            items = []
            for row in rows:
                items.append(DownloadItem(
                    id=row['id'],
                    queue_id=row['queue_id'],
                    url=row['url'],
                    title=row['title'],
                    video_id=row['video_id'],
                    uploader=row['uploader'],
                    upload_date=row['upload_date'],
                    file_path=row['file_path'],
                    file_size_bytes=row['file_size_bytes'],
                    file_hash=row['file_hash'],
                    status=row['status'],
                    error=row['error'],
                    download_started_at=row['download_started_at'],
                    download_completed_at=row['download_completed_at'],
                    download_duration_seconds=row['download_duration_seconds']
                ))
            
            return items
    
    def update_item(self, item: DownloadItem):
        """Update download item"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE download_items SET
                    file_path = ?,
                    file_size_bytes = ?,
                    file_hash = ?,
                    status = ?,
                    error = ?,
                    download_started_at = ?,
                    download_completed_at = ?,
                    download_duration_seconds = ?
                WHERE id = ?
            """, (
                item.file_path,
                item.file_size_bytes,
                item.file_hash,
                item.status,
                item.error,
                item.download_started_at,
                item.download_completed_at,
                item.download_duration_seconds,
                item.id
            ))
            conn.commit()
    
    def get_queue_stats(self, queue_id: int) -> dict:
        """Get statistics for a queue"""
        items = self.get_queue_items(queue_id)
        
        total = len(items)
        completed = sum(1 for item in items if item.status == DownloadStatus.COMPLETED.value)
        failed = sum(1 for item in items if item.status == DownloadStatus.FAILED.value)
        pending = sum(1 for item in items if item.status == DownloadStatus.PENDING.value)
        
        total_size = sum(
            item.file_size_bytes or 0 
            for item in items 
            if item.status == DownloadStatus.COMPLETED.value
        )
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'pending': pending,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
