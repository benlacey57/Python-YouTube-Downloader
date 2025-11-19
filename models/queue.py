"""Queue model"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Queue:
    """Represents a download queue for a playlist"""
    id: Optional[int]
    playlist_url: str
    playlist_title: str
    format_type: str  # 'video' or 'audio'
    quality: str
    output_dir: str
    download_order: str  # 'original', 'newest_first', 'oldest_first'
    filename_template: Optional[str] = None
    file_format: str = "mp4"  # Output format: mp4, mp3, mkv, etc.
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"
    
    # Storage settings
    storage_provider: str = "local"  # 'local' or name of configured storage
    storage_video_quality: Optional[str] = None  # Override quality for this storage
    storage_audio_quality: Optional[str] = None  # Override quality for this storage
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    @classmethod
    def from_row(cls, row):
        """Create Queue from database row"""
        return cls(
            id=row[0],
            playlist_url=row[1],
            playlist_title=row[2],
            format_type=row[3],
            quality=row[4],
            output_dir=row[5],
            download_order=row[6],
            filename_template=row[7],
            created_at=row[8],
            started_at=row[9] if len(row) > 9 else None,
            completed_at=row[10] if len(row) > 10 else None,
            status=row[11] if len(row) > 11 else "pending",
            storage_provider=row[12] if len(row) > 12 else "local",
            storage_video_quality=row[13] if len(row) > 13 else None,
            storage_audio_quality=row[14] if len(row) > 14 else None
        )
