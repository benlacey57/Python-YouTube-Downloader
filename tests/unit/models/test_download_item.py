import pytest
from typing import Optional, Tuple, Any

# Assuming the DownloadItem model is located in 'models/download_item.py'
from models.download_item import DownloadItem 

# --- Fixtures ---

@pytest.fixture
def base_item_row() -> Tuple[Any, ...]:
    """Mock database row for DownloadItem (15 fields)."""
    return (
        202,  # id
        "101",  # queue_id
        "https://example.com/video/123",  # url
        "Video Title 1",  # title
        "COMPLETED",  # status
        "/path/to/file.mp4",  # file_path
        None,  # error
        "sha256hash",  # file_hash
        "2025-11-11T10:01:00",  # download_started_at
        "2025-11-11T10:05:00",  # download_completed_at
        240.5,  # download_duration_seconds
        "2025-11-05",  # upload_date
        "Uploader Name",  # uploader
        "video123",  # video_id
        104857600  # file_size_bytes (100MB)
    )

# --- Tests ---

def test_item_instantiation():
    """Test basic instantiation with required fields."""
    item = DownloadItem(id=1, queue_id="1", url="u", title="t", status="P")
    assert item.id == 1
    assert item.status == "P"
    assert item.file_size_bytes is None

def test_item_from_row_mapping(base_item_row):
    """Test DownloadItem.from_row correctly maps all fields."""
    item = DownloadItem.from_row(base_item_row)
    
    assert item.id == 202
    assert item.title == "Video Title 1"
    assert item.status == "COMPLETED"
    assert item.file_size_bytes == 104857600
    assert item.download_duration_seconds == 240.5
    assert item.uploader == "Uploader Name"
    assert item.error is None

def test_item_prepare_for_insert():
    """Test DownloadItem.prepare_for_insert returns correct tuple order."""
    item = DownloadItem(
        id=None, queue_id="101", url="u", title="t", status="P",
        upload_date="d", uploader="up", video_id="v", file_path="p"
    )
    insert_tuple = item.prepare_for_insert()
    
    # Expected: queue_id, url, title, status, file_path, error, file_hash, started, completed, duration, upload_date, uploader, video_id, file_size
    assert len(insert_tuple) == 14
    assert insert_tuple[0] == "101" # queue_id
    assert insert_tuple[4] == "p"   # file_path
    assert insert_tuple[10] == "d"  # upload_date
    assert insert_tuple[13] is None # file_size_bytes (default None)

def test_item_prepare_for_update():
    """Test DownloadItem.prepare_for_update returns correct tuple order."""
    item = DownloadItem(
        id=300, queue_id="1", url="u", title="t", status="COMPLETED",
        file_path="/final", file_size_bytes=50, upload_date="d",
        uploader="up", video_id="v"
    )
    update_tuple = item.prepare_for_update()
    
    # Expected: status, file_path, error, file_hash, started, completed, duration, file_size_bytes, id (9 fields)
    assert len(update_tuple) == 9
    assert update_tuple[0] == "COMPLETED"
    assert update_tuple[1] == "/final"
    assert update_tuple[7] == 50  # file_size_bytes
    assert update_tuple[8] == 300 # id is last
