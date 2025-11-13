"""Channel model for monitoring"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Channel:
    """Channel model"""
    id: Optional[int]
    url: str
    title: str
    description: Optional[str] = None
    is_monitored: bool = False
    check_interval_minutes: int = 1440  # 24 hours
    last_checked_at: Optional[str] = None
    format_type: str = "video"
    quality: str = "720p"
    output_dir: str = "downloads"
    filename_template: str = "{index:03d} - {title}"
    download_order: str = "newest_first"
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Set timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
