"""Enumerations used throughout the application"""
from enum import Enum


class DownloadFormat(Enum):
    VIDEO = "video"
    AUDIO = "audio"


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadOrder(Enum):
    OLDEST_FIRST = "oldest_first"
    NEWEST_FIRST = "newest_first"
    ORIGINAL = "original"
