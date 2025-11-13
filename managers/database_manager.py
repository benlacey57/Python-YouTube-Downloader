"""Database management"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Any, Tuple
from rich.console import Console
from database.base import DatabaseConnection
from database import get_database_connection

console = Console()


class DatabaseManager:
    """Manages SQLite database operations"""
    _instance: Optional[DatabaseConnection] = None
    _config: dict = {}
    
    @classmethod
    def initialize(cls, db_type: str = "sqlite", **kwargs):
        """Initialize database connection"""
        if cls._instance is None:
            cls._config = {'db_type': db_type, **kwargs}
            cls._instance = get_database_connection(db_type, **kwargs)
    
    @classmethod
    def get_instance(cls) -> DatabaseConnection:
        """Get database instance"""
        if cls._instance is None:
            # Default to SQLite
            cls.initialize()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset database connection (for testing)"""
        cls._instance = None
        cls._config = {}
        
    def __init__(self, db_path: str = "playlist_downloader.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            console.print(f"[red]Database connection error: {e}[/red]")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def create_tables(self):
        """Create all database tables"""
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()

            # Channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    is_monitored BOOLEAN DEFAULT 0,
                    check_interval_minutes INTEGER DEFAULT 60,
                    last_checked TEXT,
                    last_video_date TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    format_type TEXT DEFAULT 'video',
                    quality TEXT DEFAULT 'best',
                    output_dir TEXT,
                    filename_template TEXT,
                    download_order TEXT DEFAULT 'original',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Queues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queues (
                    id TEXT PRIMARY KEY,
                    channel_id INTEGER,
                    playlist_url TEXT NOT NULL,
                    playlist_title TEXT NOT NULL,
                    format_type TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    output_dir TEXT NOT NULL,
                    download_order TEXT DEFAULT 'original',
                    filename_template TEXT,
                    is_monitored BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE SET NULL
                )
            """)

            # Download items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_path TEXT,
                    error TEXT,
                    file_hash TEXT,
                    download_started_at TEXT,
                    download_completed_at TEXT,
                    download_duration_seconds REAL,
                    upload_date TEXT,
                    uploader TEXT,
                    video_id TEXT,
                    file_size_bytes INTEGER,
                    FOREIGN KEY (queue_id) REFERENCES queues(id) ON DELETE CASCADE
                )
            """)

            # Daily stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    videos_downloaded INTEGER DEFAULT 0,
                    videos_queued INTEGER DEFAULT 0,
                    videos_failed INTEGER DEFAULT 0,
                    total_download_time_seconds REAL DEFAULT 0,
                    total_file_size_bytes INTEGER DEFAULT 0,
                    queues_created INTEGER DEFAULT 0,
                    queues_completed INTEGER DEFAULT 0
                )
            """)

            # Download alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threshold_bytes INTEGER UNIQUE NOT NULL,
                    last_alert_date TEXT,
                    total_size_at_alert INTEGER DEFAULT 0
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_channels_url ON channels(url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queues_channel ON queues(channel_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_queue ON download_items(queue_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_status ON download_items(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_date ON daily_stats(date)")

            self.connection.commit()
            return True

        except sqlite3.Error as e:
            console.print(f"[red]Error creating tables: {e}[/red]")
            return False

    def execute_query(self, query: str, params: Tuple = ()) -> bool:
        """Execute a query that doesn't return results"""
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            console.print(f"[red]Query error: {e}[/red]")
            self.connection.rollback()
            return False

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row"""
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            console.print(f"[red]Fetch error: {e}[/red]")
            return None

    def fetch_all(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows"""
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            console.print(f"[red]Fetch error: {e}[/red]")
            return []

    def get_last_insert_id(self) -> Optional[int]:
        """Get the last inserted row ID"""
        if not self.connection:
            return None

        try:
            cursor = self.connection.cursor()
            return cursor.lastrowid
        except sqlite3.Error:
            return None

    def begin_transaction(self):
        """Begin a transaction"""
        if self.connection:
            self.connection.execute("BEGIN")

    def commit(self):
        """Commit the current transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback the current transaction"""
        if self.connection:
            self.connection.rollback()
