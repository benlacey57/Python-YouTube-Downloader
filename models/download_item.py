"""Download item model"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DownloadItem:
    """Represents a single download item"""
    id: Optional[int]
    queue_id: str
    url: str
    title: str
    status: str
    file_path: Optional[str] = None
    error: Optional[str] = None
    file_hash: Optional[str] = None
    download_started_at: Optional[str] = None
    download_completed_at: Optional[str] = None
    download_duration_seconds: Optional[float] = None
    upload_date: Optional[str] = None
    uploader: Optional[str] = None
    video_id: Optional[str] = None
    file_size_bytes: Optional[int] = None

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
            queue_id=row[1],
            url=row[2],
            title=row[3],
            status=row[4],
            file_path=row[5],
            error=row[6],
            file_hash=row[7],
            download_started_at=row[8],
            download_completed_at=row[9],
            download_duration_seconds=row[10],
            upload_date=row[11],
            uploader=row[12],
            video_id=row[13],
            file_size_bytes=row[14]
        )

    def prepare_for_insert(self):
        """Prepare data for database insert"""
        return (
            self.queue_id,
            self.url,
            self.title,
            self.status,
            self.file_path,
            self.error,
            self.file_hash,
            self.download_started_at,
            self.download_completed_at,
            self.download_duration_seconds,
            self.upload_date,
            self.uploader,
            self.video_id,
            self.file_size_bytes
        )

    def prepare_for_update(self):
        """Prepare data for database update"""
        return (
            self.status,
            self.file_path,
            self.error,
            self.file_hash,
            self.download_started_at,
            self.download_completed_at,
            self.download_duration_seconds,
            self.file_size_bytes,
            self.id
        )
