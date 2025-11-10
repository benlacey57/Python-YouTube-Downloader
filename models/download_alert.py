"""Download alert model"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DownloadAlert:
    """Represents a download size alert threshold"""
    id: Optional[int]
    threshold_bytes: int
    last_alert_date: Optional[str] = None
    total_size_at_alert: int = 0

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
            threshold_bytes=row[1],
            last_alert_date=row[2],
            total_size_at_alert=row[3]
        )

    def prepare_for_insert(self):
        """Prepare data for database insert"""
        return (
            self.threshold_bytes,
            self.last_alert_date,
            self.total_size_at_alert
        )

    def prepare_for_update(self):
        """Prepare data for database update"""
        return (
            self.last_alert_date,
            self.total_size_at_alert,
            self.threshold_bytes
        )
