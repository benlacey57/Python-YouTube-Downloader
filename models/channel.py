"""Channel model"""
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Channel:
    """Represents a YouTube channel"""
    id: Optional[int]
    url: str
    title: str
    is_monitored: bool = False
    check_interval_minutes: int = 60
    last_checked: Optional[str] = None
    last_video_date: Optional[str] = None
    enabled: bool = True
    format_type: str = "video"
    quality: str = "best"
    output_dir: Optional[str] = None
    filename_template: Optional[str] = None
    download_order: str = "original"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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
            url=row[1],
            title=row[2],
            is_monitored=bool(row[3]),
            check_interval_minutes=row[4],
            last_checked=row[5],
            last_video_date=row[6],
            enabled=bool(row[7]),
            format_type=row[8],
            quality=row[9],
            output_dir=row[10],
            filename_template=row[11],
            download_order=row[12],
            created_at=row[13],
            updated_at=row[14]
        )

    def prepare_for_insert(self):
        """Prepare data for database insert"""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        
        return (
            self.url,
            self.title,
            int(self.is_monitored),
            self.check_interval_minutes,
            self.last_checked,
            self.last_video_date,
            int(self.enabled),
            self.format_type,
            self.quality,
            self.output_dir,
            self.filename_template,
            self.download_order,
            self.created_at,
            self.updated_at
        )

    def prepare_for_update(self):
        """Prepare data for database update"""
        self.updated_at = datetime.now().isoformat()
        
        return (
            self.title,
            int(self.is_monitored),
            self.check_interval_minutes,
            self.last_checked,
            self.last_video_date,
            int(self.enabled),
            self.format_type,
            self.quality,
            self.output_dir,
            self.filename_template,
            self.download_order,
            self.updated_at,
            self.id
        )
