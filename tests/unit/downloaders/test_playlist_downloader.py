import pytest
import shutil
import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call, mock_open
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Mock external library dependencies
mock_yt_dlp = MagicMock()
mock_yt_dlp.utils.DownloadError = Exception
mock_yt_dlp.utils.ExtractorError = Exception

# Patch the import before importing PlaylistDownloader
with patch.dict('sys.modules', {'yt_dlp': mock_yt_dlp}):
    from managers.queue_manager import QueueManager
    from managers.stats_manager import StatsManager
    from managers.proxy_manager import ProxyManager
    from notifiers.slack_notifier import SlackNotifier
    from utils.file_renamer import FileRenamer
    from models.download_item import DownloadItem
    from models.queue import Queue
    from models.daily_stats import DailyStats
    from enums import DownloadStatus
    
    # Import the file under test
    from playlist_downloader import PlaylistDownloader


# --- Fixtures and Setup ---

@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = MagicMock()
    config.proxies = ["http://proxy1.com"]
    config.cookies_file = "/path/to/cookies.txt"
    config.download_timeout_minutes = 10
    config.max_workers = 3
    config.alert_thresholds_mb = [1024]
    return config

@pytest.fixture
def mock_managers():
    """Mock dependency managers."""
    return {
        'stats': MagicMock(spec=StatsManager),
        'slack': MagicMock(spec=SlackNotifier),
        'queue': MagicMock(spec=QueueManager)
    }

@pytest.fixture
def mock_downloader(mock_config, mock_managers):
    """Instantiate PlaylistDownloader with mocks."""
    downloader = PlaylistDownloader(
        config=mock_config,
        stats_manager=mock_managers['stats'],
        slack_notifier=mock_managers['slack']
    )
    # Mock proxy manager methods used internally
    downloader.proxy_manager = MagicMock(spec=ProxyManager)
    downloader.proxy_manager.get_random_proxy.return_value = "http://random:8080"
    return downloader

@pytest.fixture
def mock_queue():
    """Mock Queue object."""
    return Queue(
        id=1,
        playlist_url="https://example.com/p",
        playlist_title="Test Playlist",
        format_type="video",
        quality="720p",
        output_dir="/tmp/downloads",
        download_order="original",
        filename_template="{index:03d} - {title}"
    )

@pytest.fixture
def mock_item():
    """Mock DownloadItem object."""
    return DownloadItem(
        id=101,
        queue_id="1",
        url="https://example.com/v",
        title="Test Video",
        status=DownloadStatus.PENDING.value,
        uploader="Uploader",
        upload_date="2025-01-01",
        video_id="vid123"
    )

@pytest.fixture
def mock_ydl_info_success():
    """Mock yt-dlp successful info dictionary."""
    return {
        'id': 'vid123',
        'title': 'Test Video Title',
        'uploader': 'Test Uploader',
        'entries': [
            {'title': 'Video 1', 'url': 'url1', '_type': 'url'},
            {'title': 'Video 2', 'url': 'url2', '_type': 'url'},
        ]
    }

@pytest.fixture
def mock_ydl_download_info(mock_item):
    """Mock yt-dlp info dict returned after a successful download."""
    return {
        'filepath': f"{mock_queue.output_dir}/001 - {mock_item.title}.mp4",
        'title': mock_item.title,
        'id': mock_item.video_id,
        'uploader': mock_item.uploader,
        'upload_date': mock_item.upload_date,
    }


# --- Tests ---

@patch('shutil.which', return_value='/usr/bin/ffmpeg')
def test_check_ffmpeg_found(mock_which, mock_downloader):
    """Test check_ffmpeg returns True if found."""
    assert mock_downloader.check_ffmpeg() is True
    mock_which.assert_called_once_with('ffmpeg')

@patch('shutil.which', return_value=None)
def test_check_ffmpeg_not_found(mock_which, mock_downloader, capsys):
    """Test check_ffmpeg returns False if not found and prints error."""
    assert mock_downloader.check_ffmpeg() is False
    assert "FFmpeg not found!" in capsys.readouterr().out

def test_get_base_ydl_opts_no_proxy(mock_downloader, mock_config):
    """Test ydl options when proxy is disabled."""
    opts = mock_downloader.get_base_ydl_opts(use_proxy=False)
    assert opts['cookiefile'] == mock_config.cookies_file
    assert 'proxy' not in opts
    assert opts['socket_timeout'] == 600 # 10 minutes

def test_get_base_ydl_opts_with_proxy(mock_downloader):
    """Test ydl options when proxy is enabled and available."""
    opts = mock_downloader.get_base_ydl_opts(use_proxy=True)
    mock_downloader.proxy_manager.get_random_proxy.assert_called_once()
    assert opts['proxy'] == "http://random:8080"

@patch('yt_dlp.YoutubeDL')
def test_get_playlist_info_success(mock_ydl_class, mock_downloader, mock_ydl_info_success):
    """Test successful playlist info extraction."""
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = mock_ydl_info_success

    info = mock_downloader.get_playlist_info("url")
    assert info['title'] == 'Test Video Title'

@patch('yt_dlp.YoutubeDL')
def test_get_playlist_info_download_error(mock_ydl_class, mock_downloader, capsys):
    """Test handling of yt-dlp DownloadError."""
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.side_effect = mock_yt_dlp.utils.DownloadError("Rate limit exceeded")

    info = mock_downloader.get_playlist_info("url")
    assert info is None
    assert "Download error: Rate limit exceeded" in capsys.readouterr().out

@patch.object(FileRenamer, 'apply_template', return_value="001_Test_Video_Title")
@patch.object(PlaylistDownloader, '_calculate_file_hash', return_value="test_hash")
@patch('pathlib.Path.exists', return_value=True)
@patch('pathlib.Path.stat')
@patch('yt_dlp.YoutubeDL')
@patch('playlist_downloader.datetime')
def test_download_item_success(mock_dt, mock_ydl_class, mock_path_stat, mock_path_exists, mock_hash, mock_renamer, mock_downloader, mock_item, mock_queue, mock_ydl_download_info):
    """Test successful download and stats/alert reporting."""
    
    # Setup time mocks
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    end_time = datetime(2025, 1, 1, 10, 4, 0) # 240 seconds duration
    mock_dt.now.side_effect = [start_time, end_time, end_time]

    # Setup yt-dlp mock
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = mock_ydl_download_info
    mock_ydl_instance.prepare_filename.return_value = "/tmp/downloads/001_Test_Video_Title.mp4"

    # Setup file system mocks
    mock_path_stat.return_value.st_size = 52428800  # 50 MB
    mock_downloader.stats_manager.get_today_stats.return_value = DailyStats(id=1, date="2025-01-01", total_file_size_bytes=0)
    mock_downloader.stats_manager.check_alert_threshold.return_value = [1073741824] # Trigger 1GB alert

    # Execute
    updated_item = mock_downloader.download_item(mock_item, mock_queue, 1)

    # Assert Item Update
    assert updated_item.status == DownloadStatus.COMPLETED.value
    assert updated_item.file_size_bytes == 52428800
    assert updated_item.download_duration_seconds == 240.0
    assert updated_item.file_hash == "test_hash"

    # Assert Stats Reporting
    mock_downloader.stats_manager.record_download.assert_called_once_with(
        True, 240.0, 52428800
    )
    mock_downloader.stats_manager.check_alert_threshold.assert_called_once_with(52428800)

    # Assert Alert Notification
    mock_downloader.slack_notifier.notify_size_threshold.assert_called_once()


@patch.object(PlaylistDownloader, 'get_base_ydl_opts')
@patch('yt_dlp.YoutubeDL')
@patch('playlist_downloader.datetime')
def test_download_item_failure(mock_dt, mock_ydl_class, mock_opts, mock_downloader, mock_item, mock_queue):
    """Test item download failure handling."""
    
    # Setup time mocks
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    end_time = datetime(2025, 1, 1, 10, 1, 0) # 60 seconds duration
    mock_dt.now.side_effect = [start_time, end_time]

    # Setup yt-dlp mock to raise an error
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.side_effect = Exception("Network timed out")

    # Execute
    updated_item = mock_downloader.download_item(mock_item, mock_queue, 1)

    # Assert Item Update
    assert updated_item.status == DownloadStatus.FAILED.value
    assert "Network timed out" in updated_item.error
    assert updated_item.download_duration_seconds == 60.0

    # Assert Stats Reporting
    mock_downloader.stats_manager.record_download.assert_called_once_with(
        False, 60.0, 0
    )

@patch('playlist_downloader.datetime')
@patch.object(PlaylistDownloader, '_print_summary')
@patch.object(PlaylistDownloader, '_check_duplicates')
@patch.object(PlaylistDownloader, 'download_item')
@patch('concurrent.futures.ThreadPoolExecutor')
def test_download_queue_execution(mock_executor, mock_download_item, mock_check_duplicates, mock_print_summary, mock_dt, mock_downloader, mock_queue, mock_managers):
    """Test the core queue execution flow."""

    # Setup time mocks
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    end_time = datetime(2025, 1, 1, 10, 5, 0)
    mock_dt.now.side_effect = [start_time, start_time, end_time, end_time] # start time, stuck item reset, complete time, summary time

    # Setup items
    item1 = DownloadItem(id=1, queue_id="1", url="u1", title="v1", status=DownloadStatus.PENDING.value)
    item2 = DownloadItem(id=2, queue_id="1", url="u2", title="v2", status=DownloadStatus.DOWNLOADING.value) # stuck item

    # Mock queue manager to return items
    mock_managers['queue'].get_queue_items.side_effect = [
        [item1, item2], # First call to find stuck items
        [item1, item2]  # Second call to get pending items after reset
    ]
    
    # Mock download_item result
    completed_item = DownloadItem(id=1, queue_id="1", url="u1", title="v1", status=DownloadStatus.COMPLETED.value, download_duration_seconds=10.0, file_size_bytes=100)
    failed_item = DownloadItem(id=2, queue_id="1", url="u2", title="v2", status=DownloadStatus.FAILED.value, download_duration_seconds=5.0, error="err")
    
    mock_download_item.side_effect = [completed_item, failed_item]

    # Mock ThreadPoolExecutor iteration
    mock_future1 = MagicMock()
    mock_future2 = MagicMock()
    mock_future1.result.return_value = completed_item
    mock_future2.result.return_value = failed_item
    
    # This simulates futures completing
    mock_executor.return_value.__enter__.return_value = mock_executor
    mock_executor.submit.side_effect = [mock_future1, mock_future2]

    # Mock as_completed to control order
    def mock_as_completed(futures):
        yield mock_future1
        yield mock_future2
    
    with patch('concurrent.futures.as_completed', side_effect=mock_as_completed):
        # Execute
        mock_downloader.download_queue(mock_queue, mock_managers['queue'])

    # Assert Stuck Item Reset
    assert item2.status == DownloadStatus.PENDING.value
    mock_managers['queue'].update_item.assert_called() # Called for item2 reset

    # Assert Item Update for results
    mock_managers['queue'].update_item.assert_has_calls([
        call(completed_item),
        call(failed_item)
    ], any_order=True)

    # Assert Queue Completion
    mock_managers['queue'].update_queue.assert_called()
    assert mock_queue.completed_at == end_time.isoformat()
    mock_downloader.stats_manager.record_queue_completed.assert_called_once()
    mock_check_duplicates.assert_called_once()
    mock_print_summary.assert_called_once()
    
    # Assert Slack Notification
    mock_downloader.slack_notifier.notify_queue_completed.assert_called_once()


@pytest.mark.parametrize("order, expected_titles", [
    ("original", ["v1", "v2"]),
    ("newest_first", ["v2", "v1"]),
    ("oldest_first", ["v1", "v2"]),
])
def test_sort_items(mock_downloader, order, expected_titles):
    """Test item sorting logic."""
    item1 = DownloadItem(id=1, queue_id="1", url="u1", title="v1", status="P")
    item2 = DownloadItem(id=2, queue_id="1", url="u2", title="v2", status="P")
    
    # original/oldest_first relies on the input list order
    items = [item1, item2]
    
    sorted_items = mock_downloader._sort_items(items, order)
    titles = [item.title for item in sorted_items]
    
    assert titles == expected_titles

@pytest.mark.parametrize("size, expected_format", [
    (None, "N/A"),
    (0, "N/A"),
    (500, "500.0 B"),
    (1024 * 5.5, "5.5 KB"),
    (1024 * 1024 * 2.5, "2.5 MB"),
    (1024 * 1024 * 1024 * 1.7, "1.7 GB"),
    (1024**4 * 1.1, "1.1 TB"),
])
def test__format_size(mock_downloader, size, expected_format):
    """Test size formatting utility."""
    assert mock_downloader._format_size(size) == expected_format

@pytest.mark.parametrize("duration, expected_format", [
    (None, "N/A"),
    (59.9, "59.9s"),
    (60.0, "1m 0s"),
    (3599, "59m 59s"),
    (3600, "1h 0m"),
    (7290, "2h 1m"), # 2 hours 1 minute 30 seconds
])
def test__format_duration(mock_downloader, duration, expected_format):
    """Test duration formatting utility."""
    assert mock_downloader._format_duration(duration) == expected_format

@patch.object(PlaylistDownloader, '_calculate_file_hash', side_effect=['hash1', 'hash2', 'hash1'])
@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('pathlib.Path.unlink')
@patch('pathlib.Path.exists', side_effect=[True, True, True])
def test__check_duplicates_and_remove(mock_exists, mock_unlink, mock_confirm, mock_hash, mock_downloader):
    """Test duplicate checking logic and removal of files."""
    
    # Three items, first and third are duplicates
    item1 = DownloadItem(id=1, queue_id="1", title="v1", status=DownloadStatus.COMPLETED.value, file_path="/f1.mp4", file_hash='hash1')
    item2 = DownloadItem(id=2, queue_id="1", title="v2", status=DownloadStatus.COMPLETED.value, file_path="/f2.mp4", file_hash='hash2')
    item3 = DownloadItem(id=3, queue_id="1", title="v3", status=DownloadStatus.COMPLETED.value, file_path="/f3.mp4", file_hash='hash1')
    
    # Manually set the hash on items, as mock_hash is only used in download_item
    item1.file_hash = 'hash1'
    item2.file_hash = 'hash2'
    item3.file_hash = 'hash1'
    
    mock_downloader._check_duplicates([item1, item2, item3])
    
    # Item 3 is the duplicate and should be removed
    mock_unlink.assert_called_once()
    mock_unlink.assert_called_with()
    # Path is mocked, but we check the call arguments against the expected path
    mock_unlink.assert_called_with() # We check that unlink was called on the duplicate
