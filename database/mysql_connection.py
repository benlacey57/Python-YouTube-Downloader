"""MySQL database connection"""
from contextlib import contextmanager
from typing import Any, List, Dict, Optional, Tuple
import mysql.connector
from mysql.connector import Error

from database.base import DatabaseConnection


class MySQLConnection(DatabaseConnection):
    """MySQL database implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 3306,
                 database: str = "downloader", user: str = "root", 
                 password: str = ""):
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.init_schema()
    
    @contextmanager
    def get_connection(self):
        """Get database connection"""
        conn = mysql.connector.connect(**self.config)
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """Fetch single row"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Fetch all rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
    
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
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    playlist_url TEXT NOT NULL,
                    playlist_title TEXT NOT NULL,
                    format_type VARCHAR(10) NOT NULL,
                    quality VARCHAR(10) NOT NULL,
                    output_dir TEXT NOT NULL,
                    filename_template TEXT NOT NULL,
                    download_order VARCHAR(20) DEFAULT 'newest_first',
                    storage_provider VARCHAR(50) DEFAULT 'local',
                    storage_video_quality VARCHAR(10),
                    storage_audio_quality VARCHAR(10),
                    created_at DATETIME NOT NULL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    status VARCHAR(20) DEFAULT 'pending',
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Download items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    queue_id INT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    video_id VARCHAR(20),
                    uploader TEXT,
                    upload_date VARCHAR(10),
                    file_path TEXT,
                    file_size_bytes BIGINT,
                    file_hash VARCHAR(64),
                    status VARCHAR(20) DEFAULT 'pending',
                    error TEXT,
                    download_started_at DATETIME,
                    download_completed_at DATETIME,
                    download_duration_seconds FLOAT,
                    INDEX idx_queue (queue_id),
                    INDEX idx_status (status),
                    FOREIGN KEY (queue_id) REFERENCES queues (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    total_downloads INT DEFAULT 0,
                    successful_downloads INT DEFAULT 0,
                    failed_downloads INT DEFAULT 0,
                    queues_completed INT DEFAULT 0,
                    total_file_size_bytes BIGINT DEFAULT 0,
                    average_file_size_bytes BIGINT DEFAULT 0,
                    INDEX idx_date (date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    is_monitored BOOLEAN DEFAULT 0,
                    check_interval_minutes INT DEFAULT 1440,
                    last_checked_at DATETIME,
                    format_type VARCHAR(10) DEFAULT 'video',
                    quality VARCHAR(10) DEFAULT '720p',
                    output_dir TEXT NOT NULL,
                    filename_template TEXT NOT NULL,
                    download_order VARCHAR(20) DEFAULT 'newest_first',
                    enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_monitored (is_monitored, enabled)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Resume info table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    queue_id INT UNIQUE NOT NULL,
                    last_downloaded_index INT NOT NULL,
                    total_items INT NOT NULL,
                    partial_downloads TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (queue_id) REFERENCES queues (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
