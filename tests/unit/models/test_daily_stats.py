import pytest
from typing import Optional, Tuple, Any

# Assuming the DailyStats model is located in 'models/daily_stats.py'
from models.daily_stats import DailyStats 

# --- Fixtures ---

@pytest.fixture
def base_stats_row() -> Tuple[Any, ...]:
    """Mock database row for DailyStats (9 fields)."""
    return (
        5,  # id
        "2025-11-11",  # date
        10,  # videos_downloaded
        20,  # videos_queued
        1,  # videos_failed
        3600.0,  # total_download_time_seconds
        5368709120,  # total_file_size_bytes (5GB)
        2,  # queues_created
        1  # queues_completed
    )

# --- Tests ---

def test_stats_instantiation():
    """Test basic instantiation with required fields and defaults."""
    stats = DailyStats(id=1, date="2025-01-01")
    assert stats.id == 1
    assert stats.videos_downloaded == 0
    assert stats.total_download_time_seconds == 0.0

def test_stats_from_row_mapping(base_stats_row):
    """Test DailyStats.from_row correctly maps all fields."""
    stats = DailyStats.from_row(base_stats_row)
    
    assert stats.id == 5
    assert stats.date == "2025-11-11"
    assert stats.videos_downloaded == 10
    assert stats.total_file_size_bytes == 5368709120
    assert stats.queues_created == 2
    assert stats.videos_failed == 1
    assert stats.total_download_time_seconds == 3600.0

def test_stats_prepare_for_insert():
    """Test DailyStats.prepare_for_insert returns correct tuple order."""
    stats = DailyStats(id=None, date="2025-12-25", videos_downloaded=5)
    insert_tuple = stats.prepare_for_insert()
    
    # Expected: date, downloaded, queued, failed, time, size, created, completed (8 fields)
    assert len(insert_tuple) == 8
    assert insert_tuple[0] == "2025-12-25" # date
    assert insert_tuple[1] == 5          # videos_downloaded
    assert insert_tuple[5] == 0          # total_file_size_bytes (default)

def test_stats_prepare_for_update():
    """Test DailyStats.prepare_for_update returns correct tuple order (date is last)."""
    stats = DailyStats(id=10, date="2025-12-25", videos_downloaded=50, queues_created=3)
    update_tuple = stats.prepare_for_update()
    
    # Expected: downloaded, queued, failed, time, size, created, completed, date (8 fields)
    assert len(update_tuple) == 8
    assert update_tuple[0] == 50  # videos_downloaded
    assert update_tuple[5] == 3   # queues_created
    assert update_tuple[7] == "2025-12-25" # date is last
