"""Queue model"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Queue:
    """Represents a download queue"""
    id: str
    channel_id: Optional[int]
    playlist_url: str
    playlist_title: str
    format_type: str
    quality: str
    output_dir: str
    download_order: str = "original"
    filename_template: Optional[str] = None
    is_monitored: bool = False
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

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
            channel_id=row[1],
            playlist_url=row[2],
            playlist_title=row[3],
            format_type=row[4],
            quality=row[5],
            output_dir=row[6],
            download_order=row[7],
            filename_template=row[8],
            is_monitored=bool(row[9]),
            created_at=row[10],
            completed_at=row[11]
        )

    def prepare_for_insert(self):
        """Prepare data for database insert"""
        return (
            self.id,
            self.channel_id,
            self.playlist_url,
            self.playlist_title,
            self.format_type,
            self.quality,
            self.output_dir,
            self.download_order,
            self.filename_template,
            int(self.is_monitored),
            self.created_at,
            self.completed_at
        )

    def prepare_for_update(self):
        """Prepare data for database update"""
        return (
            self.completed_at,
            self.id
        )
