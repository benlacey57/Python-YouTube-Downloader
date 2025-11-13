"""Enumeration types for the application"""
from enum import Enum


class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueStatus(Enum):
    """Queue status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FormatType(Enum):
    """Download format type enumeration"""
    VIDEO = "video"
    AUDIO = "audio"


class VideoQuality(Enum):
    """Video quality options"""
    BEST = "best"
    Q1080P = "1080p"
    Q720P = "720p"
    Q480P = "480p"
    Q360P = "360p"


class AudioQuality(Enum):
    """Audio quality options (kbps)"""
    Q320 = "320"
    Q256 = "256"
    Q192 = "192"
    Q128 = "128"


class StorageProvider(Enum):
    """Storage provider types"""
    LOCAL = "local"
    FTP = "ftp"
    SFTP = "sftp"
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"


class NotificationProvider(Enum):
    """Notification provider types"""
    EMAIL = "email"
    SLACK = "slack"


class DownloadOrder(Enum):
    """Download order options"""
    NEWEST_FIRST = "newest_first"
    OLDEST_FIRST = "oldest_first"
    AS_LISTED = "as_listed"
