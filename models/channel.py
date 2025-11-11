"""Channel model"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Channel:
    """Represents a monitored channel"""
    id: Optional[int]
    url: str
    title: str
    is_monitored: bool = True
    check_interval_minutes: int = 60
    last_checked: Optional[str] = None
    format_type: str = "video"
    quality: str = "720p"
    output_dir: str = "downloads"
    filename_template: Optional[str] = None
    download_order: str = "original"
    enabled: bool = True
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    @classmethod
    def from_row(cls, row):
        """Create Channel from database row"""
        return cls(
            id=row[0],
            url=row[1],
            title=row[2],
            is_monitored=bool(row[3]),
            check_interval_minutes=row[4],
            last_checked=row[5],
            format_type=row[6],
            quality=row[7],
            output_dir=row[8],
            filename_template=row[9],
            download_order=row[10],
            enabled=bool(row[11])
        )
