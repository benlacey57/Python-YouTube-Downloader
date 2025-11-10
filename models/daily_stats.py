"""Daily statistics model"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DailyStats:
    """Statistics for a single day"""
    id: Optional[int]
    date: str
    videos_downloaded: int = 0
    videos_queued: int = 0
    videos_failed: int = 0
    total_download_time_seconds: float = 0
    total_file_size_bytes: int = 0
    queues_created: int = 0
    queues_completed: int = 0

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_row(cls, row: tuple):
        """Create from database row"""
        return cls(
            id=row[0],
            date=row[1],
            videos_downloaded=row[2],
            videos_queued=row[3],
            videos_failed=row[4],
            total_download_time_seconds=row[5],
            total_file_size_bytes=row[6],
            queues_created=row[7],
            queues_completed=row[8]
        )

    def prepare_for_insert(self):
        """Prepare data for database insert"""
        return (
            self.date,
            self.videos_downloaded,
            self.videos_queued,
            self.videos_failed,
            self.total_download_time_seconds,
            self.total_file_size_bytes,
            self.queues_created,
            self.queues_completed
        )

    def prepare_for_update(self):
        """Prepare data for database update"""
        return (
            self.videos_downloaded,
            self.videos_queued,
            self.videos_failed,
            self.total_download_time_seconds,
            self.total_file_size_bytes,
            self.queues_created,
            self.queues_completed,
            self.date
        )
