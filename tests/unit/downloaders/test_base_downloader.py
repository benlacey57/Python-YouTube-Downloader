"""Tests for BaseDownloader"""
import pytest
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from downloaders.base import BaseDownloader
from managers.config_manager import AppConfig
from managers.stats_manager import StatsManager
from managers.notification_manager import NotificationManager
from models.download_item import DownloadItem
from models.queue import Queue
from enums import DownloadStatus


# Create concrete implementation for testing
class TestableDownloader(BaseDownloader):
    """Concrete implementation of BaseDownloader for testing"""
    def download_item(self, item, queue, index=0):
        return item


@pytest.fixture
def mock_config():
    """Create mock configuration"""
    config = AppConfig()
    config.max_downloads_per_hour = 50
    config.min_delay_seconds = 1.0
    config.max_delay_seconds = 2.0
    config.cookies_file = None
    config.proxies = []
    config.download_timeout_minutes = 120
    config.normalize_filenames = True
    return config


@pytest.fixture
def mock_stats_manager():
    """Create mock stats manager"""
    return Mock(spec=StatsManager)


@pytest.fixture
def mock_notification_manager():
    """Create mock notification manager"""
    manager = Mock(spec=NotificationManager)
    manager.has_any_notifier.return_value = True
    return manager


@pytest.fixture
def base_downloader(mock_config, mock_stats_manager, mock_notification_manager):
    """Create base downloader instance"""
    return TestableDownloader(
        mock_config,
        mock_stats_manager,
        mock_notification_manager
    )


@pytest.fixture
def sample_item():
    """Create sample download item"""
    return DownloadItem(
        id=1,
        queue_id=1,
        url="https://www.youtube.com/watch?v=TEST123",
        title="Test Video",
        video_id="TEST123",
        uploader="Test Channel",
        upload_date="20230101",
        file_path=None,
        file_size_bytes=None,
        file_hash=None,
        status=DownloadStatus.PENDING.value,
        error=None,
        download_started_at=None,
        download_completed_at=None,
        download_duration_seconds=None
    )


class TestBaseDownloader:
    """Test BaseDownloader functionality"""
    
    def test_init_creates_rate_limiter(self, base_downloader):
        """Test that initialization creates rate limiter"""
        assert base_downloader.rate_limiter is not None
        assert base_downloader.rate_limiter.max_downloads_per_hour == 50
    
    def test_get_base_ydl_opts_basic(self, base_downloader):
        """Test basic yt-dlp options generation"""
        opts = base_downloader.get_base_ydl_opts()
        
        assert opts['quiet'] is True
        assert opts['no_warnings'] is True
        assert opts['ignoreerrors'] is True
        assert 'extractor_args' in opts
    
    def test_get_base_ydl_opts_with_proxy(self, base_downloader):
        """Test yt-dlp options with proxy"""
        proxy = "http://proxy.example.com:8080"
        opts = base_downloader.get_base_ydl_opts(proxy=proxy)
        
        assert opts['proxy'] == proxy
    
    def test_get_base_ydl_opts_with_config_proxy(self, base_downloader, mock_config):
        """Test yt-dlp options with proxy from config"""
        mock_config.proxies = ["http://config-proxy.example.com:8080"]
        base_downloader.config = mock_config
        
        opts = base_downloader.get_base_ydl_opts()
        
        assert opts['proxy'] == mock_config.proxies[0]
    
    def test_get_base_ydl_opts_with_cookies(self, base_downloader, mock_config):
        """Test yt-dlp options with cookies file"""
        mock_config.cookies_file = "/path/to/cookies.txt"
        base_downloader.config = mock_config
        
        opts = base_downloader.get_base_ydl_opts()
        
        assert opts['cookiefile'] == "/path/to/cookies.txt"
    
    def test_get_base_ydl_opts_with_timeout(self, base_downloader, mock_config):
        """Test yt-dlp options with timeout"""
        mock_config.download_timeout_minutes = 60
        base_downloader.config = mock_config
        
        opts = base_downloader.get_base_ydl_opts()
        
        assert opts['socket_timeout'] == 3600  # 60 minutes in seconds
    
    def test_calculate_file_hash(self, base_downloader):
        """Test file hash calculation"""
        # Create temporary file with known content
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        content = b"test content"
        temp_file.write(content)
        temp_file.close()
        
        try:
            # Calculate hash
            result = base_downloader.calculate_file_hash(temp_file.name)
            
            # Calculate expected hash
            expected = hashlib.sha256(content).hexdigest()
            
            assert result == expected
        finally:
            Path(temp_file.name).unlink()
    
    def test_calculate_file_hash_nonexistent(self, base_downloader):
        """Test file hash calculation with nonexistent file"""
        result = base_downloader.calculate_file_hash("/nonexistent/file.txt")
        assert result is None
    
    def test_record_success(self, base_downloader, sample_item, mock_stats_manager, 
                           mock_notification_manager):
        """Test recording successful download"""
        start_time = datetime.now()
        sample_item.file_size_bytes = 1024000
        
        base_downloader.record_success(sample_item, start_time)
        
        # Check item status
        assert sample_item.status == DownloadStatus.COMPLETED.value
        assert sample_item.download_completed_at is not None
        assert sample_item.download_duration_seconds is not None
        assert sample_item.download_duration_seconds > 0
        
        # Check stats manager called
        mock_stats_manager.record_download.assert_called_once()
        args = mock_stats_manager.record_download.call_args[0]
        assert args[0] is True  # success
        assert args[2] == 1024000  # file_size_bytes
        
        # Check notification sent
        mock_notification_manager.notify_download_complete.assert_called_once()
    
    def test_record_failure(self, base_downloader, sample_item, mock_stats_manager,
                           mock_notification_manager):
        """Test recording failed download"""
        start_time = datetime.now()
        error_msg = "Network error"
        
        base_downloader.record_failure(sample_item, error_msg, start_time)
        
        # Check item status
        assert sample_item.status == DownloadStatus.FAILED.value
        assert sample_item.error == error_msg
        assert sample_item.download_completed_at is not None
        assert sample_item.download_duration_seconds is not None
        
        # Check stats manager called
        mock_stats_manager.record_download.assert_called_once()
        args = mock_stats_manager.record_download.call_args[0]
        assert args[0] is False  # failure
        assert args[2] == 0  # no file size for failure
        
        # Check error notification sent
        mock_notification_manager.notify_error.assert_called_once()
    
    def test_check_alerts_no_threshold(self, base_downloader, mock_stats_manager):
        """Test alert checking when no threshold is reached"""
        mock_stats_manager.check_alert_threshold.return_value = []
        
        base_downloader.check_alerts(1024000)
        
        mock_stats_manager.check_alert_threshold.assert_called_once_with(1024000)
    
    def test_check_alerts_threshold_reached(self, base_downloader, mock_stats_manager,
                                           mock_notification_manager):
        """Test alert checking when threshold is reached"""
        # Mock threshold reached
        threshold_bytes = 250 * 1024 * 1024  # 250 MB
        mock_stats_manager.check_alert_threshold.return_value = [threshold_bytes]
        
        # Mock today's stats
        mock_stats = Mock()
        mock_stats.total_file_size_bytes = 300 * 1024 * 1024  # 300 MB
        mock_stats_manager.get_today_stats.return_value = mock_stats
        
        base_downloader.check_alerts(1024000)
        
        # Check notification sent
        mock_notification_manager.notify_size_threshold.assert_called_once()
        args = mock_notification_manager.notify_size_threshold.call_args[0]
        assert args[0] == 250  # threshold in MB
    
    @patch('yt_dlp.YoutubeDL')
    def test_get_playlist_info_success(self, mock_ydl_class, base_downloader):
        """Test getting playlist information successfully"""
        # Mock yt-dlp response
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Playlist',
            'playlist_count': 10,
            'entries': []
        }
        mock_ydl_class.return_value = mock_ydl
        
        result = base_downloader.get_playlist_info(
            "https://www.youtube.com/playlist?list=TEST123"
        )
        
        assert result is not None
        assert result['title'] == 'Test Playlist'
        assert result['playlist_count'] == 10
    
    @patch('yt_dlp.YoutubeDL')
    def test_get_playlist_info_failure(self, mock_ydl_class, base_downloader):
        """Test getting playlist information with error"""
        # Mock yt-dlp to raise exception
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")
        mock_ydl_class.return_value = mock_ydl
        
        result = base_downloader.get_playlist_info(
            "https://www.youtube.com/playlist?list=TEST123"
        )
        
        assert result is None
    
    def test_record_success_without_stats_manager(self, mock_config, sample_item):
        """Test recording success without stats manager"""
        downloader = TestableDownloader(mock_config, None, None)
        start_time = datetime.now()
        sample_item.file_size_bytes = 1024000
        
        # Should not raise exception
        downloader.record_success(sample_item, start_time)
        
        assert sample_item.status == DownloadStatus.COMPLETED.value
    
    def test_record_failure_without_notification_manager(self, mock_config, sample_item):
        """Test recording failure without notification manager"""
        downloader = TestableDownloader(mock_config, None, None)
        start_time = datetime.now()
        
        # Should not raise exception
        downloader.record_failure(sample_item, "Test error", start_time)
        
        assert sample_item.status == DownloadStatus.FAILED.value
        assert sample_item.error == "Test error"
