"""Shared test fixtures and configuration"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from models.queue import Queue
from models.download_item import DownloadItem
from models.channel import Channel
from models.daily_stats import DailyStats
from enums import DownloadStatus


# ===== Mock Rich Console =====
@pytest.fixture(scope="session", autouse=True)
def mock_rich_console():
    """Mock rich console globally to prevent output during tests"""
    with patch('rich.console.Console'):
        yield


# ===== Configuration Fixtures =====
@pytest.fixture
def mock_config():
    """Mock configuration object with default values"""
    config = MagicMock()
    config.proxies = ["http://proxy1:8080", "http://proxy2:8080"]
    config.proxy_rotation_enabled = True
    config.proxy_rotation_frequency = 5
    config.cookies_file = "/path/to/cookies.txt"
    config.download_timeout_minutes = 10
    config.max_workers = 3
    config.alert_thresholds_mb = [1024, 5120]
    config.min_delay_seconds = 2.0
    config.max_delay_seconds = 5.0
    config.max_downloads_per_hour = 50
    config.bandwidth_limit_mbps = None
    config.normalize_filenames = True
    config.default_video_quality = "720p"
    config.default_audio_quality = "192"
    config.setup_completed = True
    config.auto_record_live_streams = False
    # Notification settings
    config.slack_webhook_url = None
    config.email_enabled = False
    config.email_settings = {}
    config.daily_summary_enabled = False
    config.weekly_stats_enabled = False
    return config


@pytest.fixture
def mock_config_manager(mock_config):
    """Mock ConfigManager with a config attribute"""
    manager = MagicMock()
    manager.config = mock_config
    manager.save_config = MagicMock()
    return manager


# ===== Model Fixtures =====
@pytest.fixture
def sample_queue():
    """Create a sample Queue object"""
    return Queue(
        id=1,
        playlist_url="https://example.com/playlist",
        playlist_title="Test Playlist",
        format_type="video",
        quality="720p",
        output_dir="/tmp/downloads",
        filename_template="{index:03d} - {title}",
        download_order="newest_first",
        storage_provider="local",
        storage_video_quality=None,
        storage_audio_quality=None,
        created_at=datetime.now().isoformat(),
        started_at=None,
        completed_at=None,
        status="pending"
    )


@pytest.fixture
def sample_download_item():
    """Create a sample DownloadItem object"""
    return DownloadItem(
        id=1,
        queue_id=1,
        url="https://example.com/video",
        title="Test Video",
        video_id="test123",
        uploader="Test Uploader",
        upload_date="20250101",
        file_path=None,
        file_size_bytes=None,
        file_hash=None,
        status=DownloadStatus.PENDING.value,
        error=None,
        download_started_at=None,
        download_completed_at=None,
        download_duration_seconds=None
    )


@pytest.fixture
def sample_channel():
    """Create a sample Channel object"""
    return Channel(
        id=1,
        url="https://example.com/channel",
        title="Test Channel",
        is_monitored=True,
        check_interval_minutes=60,
        format_type="video",
        quality="720p",
        output_dir="/tmp/downloads/channel",
        filename_template="{index:03d} - {title}",
        download_order="newest_first",
        enabled=True
    )


@pytest.fixture
def sample_daily_stats():
    """Create a sample DailyStats object"""
    return DailyStats(
        id=1,
        date="2025-11-21",
        total_downloads=10,
        successful_downloads=8,
        failed_downloads=2,
        total_file_size_bytes=1073741824,  # 1 GB
        average_download_speed_mbps=5.0,
        total_download_time_seconds=600
    )


# ===== Manager Fixtures =====
@pytest.fixture
def mock_stats_manager():
    """Mock StatsManager"""
    manager = MagicMock()
    manager.record_download = MagicMock()
    manager.record_queue_completed = MagicMock()
    manager.get_today_stats = MagicMock(return_value=DailyStats(
        id=1,
        date=datetime.now().strftime("%Y-%m-%d"),
        total_downloads=0,
        successful_downloads=0,
        failed_downloads=0,
        total_file_size_bytes=0,
        average_download_speed_mbps=0.0,
        total_download_time_seconds=0
    ))
    return manager


@pytest.fixture
def mock_queue_manager():
    """Mock QueueManager"""
    manager = MagicMock()
    manager.get_queue = MagicMock()
    manager.get_all_queues = MagicMock(return_value=[])
    manager.get_queue_items = MagicMock(return_value=[])
    manager.update_item = MagicMock()
    manager.update_queue = MagicMock()
    manager.create_queue = MagicMock(return_value=1)
    manager.add_item = MagicMock(return_value=1)
    return manager


@pytest.fixture
def mock_notification_manager():
    """Mock NotificationManager"""
    manager = MagicMock()
    manager.has_any_notifier = MagicMock(return_value=False)
    manager.notify_queue_completed = MagicMock()
    manager.notify_download_failed = MagicMock()
    return manager


@pytest.fixture
def mock_proxy_manager():
    """Mock ProxyManager"""
    manager = MagicMock()
    manager.get_next_proxy = MagicMock(return_value="http://proxy:8080")
    manager.get_random_proxy = MagicMock(return_value="http://proxy:8080")
    manager.has_proxies = MagicMock(return_value=True)
    manager.get_all_proxies = MagicMock(return_value=["http://proxy1:8080", "http://proxy2:8080"])
    return manager


# ===== File System Fixtures =====
@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for tests"""
    test_dir = tmp_path / "test_downloads"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def mock_file_operations():
    """Mock common file operations"""
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.unlink'), \
         patch('pathlib.Path.stat') as mock_stat:
        
        mock_stat.return_value.st_size = 1024 * 1024  # 1 MB
        yield


# ===== YT-DLP Fixtures =====
@pytest.fixture
def mock_yt_dlp():
    """Mock yt_dlp module"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info = MagicMock(return_value={
            'id': 'test123',
            'title': 'Test Video',
            'uploader': 'Test Uploader',
            'upload_date': '20250101',
            'entries': []
        })
        mock_instance.prepare_filename = MagicMock(return_value='/tmp/test.mp4')
        yield mock_ydl


# ===== Network Fixtures =====
@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={})
        mock_response.text = "OK"
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }


# ===== Time Fixtures =====
@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent time-based tests"""
    fixed_time = datetime(2025, 11, 21, 12, 0, 0)
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt
