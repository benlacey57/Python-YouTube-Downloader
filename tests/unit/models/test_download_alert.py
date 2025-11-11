import pytest
from typing import Optional, Tuple, Any

# Assuming the DownloadAlert model is located in 'models/download_alert.py'
from models.download_alert import DownloadAlert 

# --- Fixtures ---

@pytest.fixture
def base_alert_row() -> Tuple[Any, ...]:
    """Mock database row for DownloadAlert (4 fields)."""
    return (
        8,  # id
        1073741824,  # threshold_bytes (1GB)
        "2025-11-10",  # last_alert_date
        500000000  # total_size_at_alert
    )

# --- Tests ---

def test_alert_instantiation():
    """Test basic instantiation with required fields and defaults."""
    alert = DownloadAlert(id=1, threshold_bytes=1000)
    assert alert.id == 1
    assert alert.threshold_bytes == 1000
    assert alert.last_alert_date is None
    assert alert.total_size_at_alert == 0

def test_alert_from_row_mapping(base_alert_row):
    """Test DownloadAlert.from_row correctly maps all fields."""
    alert = DownloadAlert.from_row(base_alert_row)
    
    assert alert.id == 8
    assert alert.threshold_bytes == 1073741824
    assert alert.last_alert_date == "2025-11-10"
    assert alert.total_size_at_alert == 500000000

def test_alert_prepare_for_insert():
    """Test DownloadAlert.prepare_for_insert returns correct tuple order."""
    alert = DownloadAlert(id=None, threshold_bytes=100)
    insert_tuple = alert.prepare_for_insert()
    
    # Expected: threshold_bytes, last_alert_date, total_size_at_alert (3 fields)
    assert len(insert_tuple) == 3
    assert insert_tuple[0] == 100
    assert insert_tuple[1] is None
    assert insert_tuple[2] == 0

def test_alert_prepare_for_update():
    """Test DownloadAlert.prepare_for_update returns correct tuple order (threshold is last)."""
    alert = DownloadAlert(id=1, threshold_bytes=200, last_alert_date="today", total_size_at_alert=50)
    update_tuple = alert.prepare_for_update()
    
    # Expected: last_alert_date, total_size_at_alert, threshold_bytes (3 fields)
    assert len(update_tuple) == 3
    assert update_tuple[0] == "today"
    assert update_tuple[2] == 200 # threshold_bytes is last
