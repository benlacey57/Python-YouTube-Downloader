import pytest
from unittest.mock import patch, MagicMock
from stats_display import StatsDisplay
from models.daily_stats import DailyStats
from models.channel import Channel

# --- Fixtures and Mocks ---

@pytest.fixture
def mock_managers():
    """Mock required manager dependencies for testing data retrieval."""
    mock_stats_manager = MagicMock()
    mock_queue_manager = MagicMock()
    mock_monitor_manager = MagicMock()

    # Mock return values for display_statistics
    mock_stats_manager.get_summary.side_effect = [
        # summary_7 (Last 7 Days)
        {
            'total_downloaded': 50,
            'total_queued': 100,
            'total_failed': 5,
            'avg_downloads_per_day': 7.14,
            'total_size_bytes': 2 * 1024**3 # 2 GB
        },
        # summary_30 (Last 30 Days)
        {
            'total_downloaded': 150,
            'total_queued': 300,
            'total_failed': 15,
            'avg_downloads_per_day': 5.0,
            'total_size_bytes': 10 * 1024**3 # 10 GB
        }
    ]
    
    # Mock return value for get_date_range_stats (Last 14 Days)
    mock_stats_manager.get_date_range_stats.return_value = [
        DailyStats(id=1, date="2025-10-31", videos_downloaded=10, videos_failed=0, total_download_time_seconds=3600, total_file_size_bytes=1000),
        DailyStats(id=2, date="2025-11-01", videos_downloaded=0, videos_failed=2, total_download_time_seconds=0, total_file_size_bytes=0),
    ]

    # Mock return values for display_dashboard
    mock_queue_manager.get_statistics.return_value = {
        'total_queues': 5, 'completed_items': 100, 'pending_items': 50,
        'failed_items': 10, 'total_time': 7200 # 2 hours
    }
    mock_monitor_manager.is_running = True
    mock_monitor_manager.get_all_channels.return_value = [
        Channel(id=1, url="u1", title="c1", is_monitored=True),
        Channel(id=2, url="u2", title="c2", is_monitored=False),
    ]
    
    return {
        "stats_manager": mock_stats_manager,
        "queue_manager": mock_queue_manager,
        "monitor_manager": mock_monitor_manager,
    }


@pytest.fixture
def mock_rich_print(monkeypatch):
    """Mocks rich.console.Console.print for silencing/checking output."""
    mock_print = MagicMock()
    monkeypatch.setattr("stats_display.console.print", mock_print)
    return mock_print


# --- Test Utility Methods ---

def test_format_duration():
    """Test _format_duration conversion."""
    assert StatsDisplay._format_duration(30) == "30.0s"
    assert StatsDisplay._format_duration(90) == "1m 30s"
    assert StatsDisplay._format_duration(3661) == "1h 1m"
    assert StatsDisplay._format_duration(None) == "N/A"
    assert StatsDisplay._format_duration(0) == "N/A"


def test_format_size():
    """Test _format_size conversion."""
    assert StatsDisplay._format_size(500) == "500.0 B"
    assert StatsDisplay._format_size(1536) == "1.5 KB"
    assert StatsDisplay._format_size(1048576 * 2.5) == "2.5 MB"
    assert StatsDisplay._format_size(1024**3 * 4) == "4.0 GB"
    assert StatsDisplay._format_size(None) == "N/A"
    assert StatsDisplay._format_size(0) == "N/A"


# --- Test display_statistics ---

def test_display_statistics_calls_managers_and_prints_tables(mock_rich_print, mock_managers):
    """Verify that manager data retrieval methods are called and tables are printed."""
    
    StatsDisplay.display_statistics(mock_managers["stats_manager"], mock_managers["queue_manager"])
    
    # Assert data retrieval
    mock_managers["stats_manager"].get_summary.assert_any_call(7)
    mock_managers["stats_manager"].get_summary.assert_any_call(30)
    mock_managers["stats_manager"].get_date_range_stats.assert_called_once_with(14)
    
    # Assert printing the two tables (Summary and Daily)
    assert mock_rich_print.call_count >= 5 # 2 newlines + 2 tables + 1 header newline

    # Verify formatting of key data points in the output
    output_str = str(mock_rich_print.call_args_list)
    
    # Check Summary Table data (7 days)
    assert "7.1" in output_str # Avg/Day
    assert "2.0 GB" in output_str # Total Size

    # Check Daily Table data (Last 14 Days)
    assert "2025-10-31" in output_str
    assert "1h 0m" in output_str
    assert "0" in output_str
    assert "1.0 KB" in output_str # total_file_size_bytes=1000


# --- Test display_dashboard ---

@patch("stats_display.Layout")
def test_display_dashboard_calls_managers_and_creates_layout(mock_layout_class, mock_managers):
    """Verify data retrieval for the dashboard panels and layout structure."""
    
    StatsDisplay.display_dashboard(
        mock_managers["queue_manager"],
        mock_managers["monitor_manager"],
        mock_managers["stats_manager"]
    )
    
    # Assert data retrieval
    mock_managers["queue_manager"].get_statistics.assert_called_once()
    mock_managers["stats_manager"].get_summary.assert_called_once_with(7)
    mock_managers["monitor_manager"].get_all_channels.assert_called_once()
    
    # Assert layout structure (mock_layout_class is the Layout constructor)
    mock_layout_class.assert_called_once()
    mock_layout_instance = mock_layout_class.return_value
    mock_layout_instance.split_row.assert_called_once()
    
    # Check content of one panel (e.g., Queue Statistics Panel)
    output_str = str(mock_layout_instance.split_row.call_args)
    assert "Total Queues: 5" in output_str
    assert "Pending: 50" in output_str
    assert "Total Time: 2h 0m" in output_str
    
    # Check content of Monitoring Panel
    assert "Status: Running" in output_str
    assert "Monitored Channels: 1" in output_str
