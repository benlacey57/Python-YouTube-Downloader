"""SQLite database connection"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Any, List, Dict, Optional, Tuple

from database.base import DatabaseConnection


class SQLiteConnection(DatabaseConnection):
    """SQLite database implementation"""
    
    def __init__(self, db_path: str = "data/downloader.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()
    
    @contextmanager
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute(self, query: str, params: Tuple = ()) -> Any:
        """Execute query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """Fetch single row"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Fetch all rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def insert(self, query: str, params: Tuple = ()) -> int:
        """Insert and return last row ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def update(self, query: str, params: Tuple = ()) -> int:
        """Update and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    
    def delete(self, query: str, params: Tuple = ()) -> int:
        """Delete and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    
    def init_schema(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
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
                    filename_template TEXT NOT NULL,
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
            
            # Statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_downloads INTEGER DEFAULT 0,
                    successful_downloads INTEGER DEFAULT 0,
                    failed_downloads INTEGER DEFAULT 0,
                    queues_completed INTEGER DEFAULT 0,
                    total_file_size_bytes INTEGER DEFAULT 0,
                    average_file_size_bytes INTEGER DEFAULT 0
                )
            """)
            
            # Channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    is_monitored BOOLEAN DEFAULT 0,
                    check_interval_minutes INTEGER DEFAULT 1440,
                    last_checked_at TEXT,
                    format_type TEXT DEFAULT 'video',
                    quality TEXT DEFAULT '720p',
                    output_dir TEXT NOT NULL,
                    filename_template TEXT NOT NULL,
                    download_order TEXT DEFAULT 'newest_first',
                    enabled BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Resume info table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id INTEGER UNIQUE NOT NULL,
                    last_downloaded_index INTEGER NOT NULL,
                    total_items INTEGER NOT NULL,
                    partial_downloads TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (queue_id) REFERENCES queues (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queues_status ON queues(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_queue ON download_items(queue_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_status ON download_items(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_date ON statistics(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_channels_monitored ON channels(is_monitored, enabled)")
