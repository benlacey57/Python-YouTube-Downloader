import pytest
from datetime import datetime
from unittest.mock import patch
from typing import Optional, Tuple, Any

# Assuming the Channel model is located in 'models/channel.py'
from models.channel import Channel 

# --- Fixtures ---

@pytest.fixture
def mock_datetime_now():
    """Patches datetime.now() for deterministic timestamp testing."""
    test_time = datetime(2025, 11, 11, 10, 30, 0)
    test_iso = test_time.isoformat()
    # Patch datetime.now() within the Channel module
    with patch('models.channel.datetime') as mock_dt: 
        mock_dt.now.return_value = test_time
        mock_dt.now.return_value.isoformat.return_value = test_iso
        yield test_iso

@pytest.fixture
def base_channel_row() -> Tuple[Any, ...]:
    """Mock database row for Channel (15 fields)."""
    return (
        1,  # id
        "https://example.com/channel/abc",  # url
        "Test Channel Title",  # title
        1,  # is_monitored (True)
        60,  # check_interval_minutes
        "2025-11-10T10:00:00",  # last_checked
        "2025-11-09",  # last_video_date
        0,  # enabled (False)
        "audio",  # format_type
        "320",  # quality
        "/downloads/channel",  # output_dir
        "{title}",  # filename_template
        "newest_first",  # download_order
        "2025-01-01T00:00:00",  # created_at
        "2025-11-11T10:00:00"  # updated_at
    )

# --- Tests ---

def test_channel_instantiation():
    """Test basic instantiation with required fields."""
    channel = Channel(id=5, url="test_url", title="Test Title")
    assert channel.id == 5
    assert channel.is_monitored is False
    assert channel.enabled is True
    assert channel.quality == "best"

def test_channel_from_row_mapping(base_channel_row):
    """Test Channel.from_row correctly maps and converts types (especially bools)."""
    channel = Channel.from_row(base_channel_row)
    
    assert channel.id == 1
    assert channel.title == "Test Channel Title"
    assert channel.is_monitored is True  # Check boolean conversion (1 -> True)
    assert channel.enabled is False      # Check boolean conversion (0 -> False)
    assert channel.check_interval_minutes == 60
    assert channel.format_type == "audio"
    assert channel.created_at == "2025-01-01T00:00:00"

def test_channel_prepare_for_insert(mock_datetime_now):
    """Test Channel.prepare_for_insert returns correct tuple order and sets timestamps."""
    channel = Channel(
        id=None, url="url", title="Title", is_monitored=True,
        output_dir=".", created_at=None
    )
    insert_tuple = channel.prepare_for_insert()
    
    # Expected order: url, title, is_monitored(int), check_interval, last_checked, last_video, enabled(int), format, quality, output_dir, filename_template, download_order, created_at, updated_at
    assert len(insert_tuple) == 14
    assert insert_tuple[2] == 1  # is_monitored (True -> 1)
    assert insert_tuple[6] == 1  # enabled (Default True -> 1)
    assert insert_tuple[12] == mock_datetime_now  # created_at set
    assert insert_tuple[13] == mock_datetime_now  # updated_at set

def test_channel_prepare_for_update(mock_datetime_now):
    """Test Channel.prepare_for_update returns correct tuple order and sets updated_at."""
    channel = Channel(
        id=50, url="url", title="New Title", is_monitored=False,
        output_dir="/new", created_at="old_time"
    )
    update_tuple = channel.prepare_for_update()
    
    # Expected order: title, is_monitored(int), check_interval, last_checked, last_video, enabled(int), format, quality, output_dir, filename_template, download_order, updated_at, id
    assert len(update_tuple) == 13
    assert update_tuple[0] == "New Title"
    assert update_tuple[1] == 0  # is_monitored (False -> 0)
    assert update_tuple[5] == 1  # enabled (Default True -> 1)
    assert update_tuple[11] == mock_datetime_now  # updated_at set
    assert update_tuple[12] == 50  # id is last
