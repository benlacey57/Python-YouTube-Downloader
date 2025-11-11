"""Queue management operations"""
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models.queue import Queue
from models.download_item import DownloadItem
from enums import DownloadStatus


class QueueManager:
    """Manages download queues in database"""
    
    def __init__(self, db_path: str = "downloads.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
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
                    download_order TEXT NOT NULL,
                    filename_template TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    storage_provider TEXT DEFAULT 'local',
                    storage_video_quality TEXT,
                    storage_audio_quality TEXT
                )
            """)
            
            # Check if storage columns exist, add them if not
            cursor.execute("PRAGMA table_info(queues)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'storage_provider' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN storage_provider TEXT DEFAULT 'local'")
            
            if 'storage_video_quality' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN storage_video_quality TEXT")
            
            if 'storage_audio_quality' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN storage_audio_quality TEXT")
            
            # Download items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_path TEXT,
                    file_size_bytes INTEGER,
                    file_hash TEXT,
                    download_started_at TEXT,
                    download_completed_at TEXT,
                    download_duration_seconds REAL,
                    error TEXT,
                    uploader TEXT,
                    upload_date TEXT,
                    video_id TEXT,
                    FOREIGN KEY (queue_id) REFERENCES queues (id)
                )
            """)
            
            conn.commit()
    
    def create_queue(self, queue: Queue) -> Queue:
        """Create a new download queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO queues (
                    playlist_url, playlist_title, format_type, quality,
                    output_dir, download_order, filename_template, created_at,
                    storage_provider, storage_video_quality, storage_audio_quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                queue.playlist_url,
                queue.playlist_title,
                queue.format_type,
                queue.quality,
                queue.output_dir,
                queue.download_order,
                queue.filename_template,
                datetime.now().isoformat(),
                queue.storage_provider,
                queue.storage_video_quality,
                queue.storage_audio_quality
            ))
            
            queue.id = cursor.lastrowid
            conn.commit()
            
            return queue
    
    def get_queue(self, queue_id: int) -> Optional[Queue]:
        """Get queue by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM queues WHERE id = ?", (queue_id,))
            row = cursor.fetchone()
            
            if row:
                return Queue.from_row(row)
            return None
    
    def get_all_queues(self) -> List[Queue]:
        """Get all queues"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM queues ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            return [Queue.from_row(row) for row in rows]
    
    def get_incomplete_queues(self) -> List[Queue]:
        """Get queues that haven't been completed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM queues 
                WHERE completed_at IS NULL 
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            
            return [Queue.from_row(row) for row in rows]
    
    def update_queue(self, queue: Queue):
        """Update queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE queues 
                SET playlist_title = ?, format_type = ?, quality = ?,
                    output_dir = ?, download_order = ?, filename_template = ?,
                    completed_at = ?, storage_provider = ?,
                    storage_video_quality = ?, storage_audio_quality = ?
                WHERE id = ?
            """, (
                queue.playlist_title,
                queue.format_type,
                queue.quality,
                queue.output_dir,
                queue.download_order,
                queue.filename_template,
                queue.completed_at,
                queue.storage_provider,
                queue.storage_video_quality,
                queue.storage_audio_quality,
                queue.id
            ))
            conn.commit()
    
    def add_item_to_queue(self, item: DownloadItem) -> DownloadItem:
        """Add download item to queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO download_items (
                    queue_id, url, title, status, uploader, upload_date, video_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.queue_id,
                item.url,
                item.title,
                item.status,
                item.uploader,
                item.upload_date,
                item.video_id
            ))
            
            item.id = cursor.lastrowid
            conn.commit()
            
            return item
    
    def get_queue_items(self, queue_id: int) -> List[DownloadItem]:
        """Get all items for a queue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM download_items 
                WHERE queue_id = ?
                ORDER BY id
            """, (queue_id,))
            rows = cursor.fetchall()
            
            return [DownloadItem.from_row(row) for row in rows]
    
    def update_item(self, item: DownloadItem):
        """Update download item"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE download_items 
                SET status = ?, file_path = ?, file_size_bytes = ?,
                    file_hash = ?, download_started_at = ?,
                    download_completed_at = ?, download_duration_seconds = ?,
                    error = ?, uploader = ?, upload_date = ?, video_id = ?
                WHERE id = ?
            """, (
                item.status,
                item.file_path,
                item.file_size_bytes,
                item.file_hash,
                item.download_started_at,
                item.download_completed_at,
                item.download_duration_seconds,
                item.error,
                item.uploader,
                item.upload_date,
                item.video_id,
                item.id
            ))
            conn.commit()
    
    def delete_queue(self, queue_id: int):
        """Delete queue and all its items"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete items
            cursor.execute("DELETE FROM download_items WHERE queue_id = ?", (queue_id,))
            
            # Delete queue
            cursor.execute("DELETE FROM queues WHERE id = ?", (queue_id,))
            
            conn.commit()
