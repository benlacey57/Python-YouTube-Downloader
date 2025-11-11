import pytest
from typing import Optional, Tuple, Any

# Assuming the Queue model is located in 'models/queue.py'
from models.queue import Queue 

# --- Fixtures ---

@pytest.fixture
def base_queue_row() -> Tuple[Any, ...]:
    """Mock database row for Queue (13 fields, including storage)."""
    return (
        101,  # id
        "https://example.com/playlist/xyz",  # playlist_url
        "My Test Playlist",  # playlist_title
        "video",  # format_type
        "1080p",  # quality
        "/output/queue",  # output_dir
        "oldest_first",  # download_order
        "{index} - {title}",  # filename_template
        "2025-11-01T00:00:00",  # created_at
        None,  # completed_at
        "dropbox",  # storage_provider (row[10])
        "720p",  # storage_video_quality (row[11])
        "128"  # storage_audio_quality (row[12])
    )

# --- Tests ---

def test_queue_instantiation():
    """Test basic instantiation with required fields."""
    queue = Queue(id=1, playlist_url="url", playlist_title="title", 
                  format_type="video", quality="720p", output_dir=".", 
                  download_order="original")
    assert queue.id == 1
    assert queue.storage_provider == "local"
    assert queue.storage_video_quality is None

def test_queue_from_row_full_mapping(base_queue_row):
    """Test Queue.from_row with all fields present (including storage)."""
    queue = Queue.from_row(base_queue_row)
    
    assert queue.id == 101
    assert queue.playlist_title == "My Test Playlist"
    assert queue.quality == "1080p"
    assert queue.storage_provider == "dropbox"
    assert queue.storage_video_quality == "720p"
    assert queue.storage_audio_quality == "128"

def test_queue_from_row_legacy_mapping():
    """Test Queue.from_row with a legacy row (missing storage fields)."""
    # A row with only the first 10 mandatory fields
    legacy_row = (101, "url", "Title", "video", "1080p", "dir", "order", "template", "c_at", "comp_at")
    queue = Queue.from_row(legacy_row)
    
    # Check that defaults/None are applied for missing fields
    assert queue.playlist_url == "url"
    assert queue.completed_at == "comp_at"
    assert queue.storage_provider == "local"
    assert queue.storage_video_quality is None
    assert queue.storage_audio_quality is None

def test_queue_to_dict():
    """Test to_dict conversion."""
    queue = Queue(id=1, playlist_url="u", playlist_title="t", 
                  format_type="a", quality="q", output_dir="d", 
                  download_order="o", completed_at="now")
    d = queue.to_dict()
    assert d['id'] == 1
    assert d['completed_at'] == "now"
    assert 'storage_provider' in d
