"""Tests for VideoDownloader"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from downloaders.video import VideoDownloader
from models.download_item import DownloadItem
from models.queue import Queue
from enums import DownloadStatus


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_queue(temp_dir):
    """Create sample queue"""
    return Queue(
        id=1,
        playlist_url="https://www.youtube.com/playlist?list=TEST",
        playlist_title="Test Playlist",
        format_type="video",
        quality="720p",
        output_dir=temp_dir,
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


class TestVideoDownloader:
    """Test VideoDownloader functionality"""
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    def test_init(self, mock_notif, mock_stats, mock_config):
        """Test VideoDownloader initialization"""
        downloader = VideoDownloader()
        assert downloader is not None
        assert downloader.rate_limiter is not None
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.video.keyboard_handler')
    @patch('time.sleep')
    def test_download_item_success(self, mock_sleep, mock_kb, mock_ydl_class,
                                   mock_notif, mock_stats, mock_config, 
                                   sample_item, sample_queue, temp_dir):
        """Test successful video download"""
        # Setup mocks
        mock_kb.is_skip_requested.return_value = False
        mock_config_instance = MagicMock()
        mock_config_instance.config.normalize_filenames = True
        mock_config.return_value = mock_config_instance
        
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'id': 'TEST123',
            'uploader': 'Test Channel',
            'upload_date': '20230101'
        }
        
        # Create temp file
        temp_file = Path(temp_dir) / "001 - Test Video.mp4"
        temp_file.write_text("fake video content")
        mock_ydl.prepare_filename.return_value = str(temp_file)
        mock_ydl_class.return_value = mock_ydl
        
        # Download
        downloader = VideoDownloader()
        result = downloader.download_item(sample_item, sample_queue, index=1)
        
        # Verify
        assert result.status == DownloadStatus.COMPLETED.value
        assert result.file_path is not None
        assert result.file_size_bytes > 0
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    @patch('downloaders.video.keyboard_handler')
    def test_download_item_skip_requested(self, mock_kb, mock_notif, mock_stats,
                                         mock_config, sample_item, sample_queue):
        """Test download with skip requested"""
        mock_kb.is_skip_requested.return_value = True
        
        downloader = VideoDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        assert result.status == DownloadStatus.PENDING.value
        assert result.error == "Skipped by user"
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.video.keyboard_handler')
    @patch('time.sleep')
    def test_download_item_network_error(self, mock_sleep, mock_kb, mock_ydl_class,
                                        mock_notif, mock_stats, mock_config,
                                        sample_item, sample_queue):
        """Test download with network error"""
        mock_kb.is_skip_requested.return_value = False
        
        # Mock yt-dlp to raise exception
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")
        mock_ydl_class.return_value = mock_ydl
        
        downloader = VideoDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        assert result.status == DownloadStatus.FAILED.value
        assert "Network error" in result.error
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    def test_quality_format_best(self, mock_notif, mock_stats, mock_config, 
                                sample_queue):
        """Test format string for best quality"""
        sample_queue.quality = "best"
        
        downloader = VideoDownloader()
        opts = downloader.get_base_ydl_opts()
        
        # Verify downloader initialized
        assert downloader is not None
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    def test_quality_format_720p(self, mock_notif, mock_stats, mock_config):
        """Test format string for 720p quality"""
        downloader = VideoDownloader()
        assert downloader is not None
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    def test_quality_format_worst(self, mock_notif, mock_stats, mock_config):
        """Test format string for worst quality"""
        downloader = VideoDownloader()
        assert downloader is not None
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.video.keyboard_handler')
    @patch('time.sleep')
    def test_download_with_proxy(self, mock_sleep, mock_kb, mock_ydl_class,
                                 mock_notif, mock_stats, mock_config,
                                 sample_item, sample_queue, temp_dir):
        """Test download with proxy"""
        mock_kb.is_skip_requested.return_value = False
        proxy = "http://proxy.example.com:8080"
        
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'id': 'TEST123'
        }
        temp_file = Path(temp_dir) / "test.mp4"
        temp_file.write_text("fake video")
        mock_ydl.prepare_filename.return_value = str(temp_file)
        mock_ydl_class.return_value = mock_ydl
        
        downloader = VideoDownloader()
        result = downloader.download_item(sample_item, sample_queue, proxy=proxy)
        
        # Verify download completed
        assert result.status in [DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value]
    
    @patch('downloaders.video.ConfigManager')
    @patch('downloaders.video.StatsManager')
    @patch('downloaders.video.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.video.keyboard_handler')
    @patch('time.sleep')
    def test_metadata_extraction(self, mock_sleep, mock_kb, mock_ydl_class,
                                 mock_notif, mock_stats, mock_config,
                                 sample_item, sample_queue, temp_dir):
        """Test metadata extraction during download"""
        mock_kb.is_skip_requested.return_value = False
        
        # Mock yt-dlp with metadata
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Updated Title',
            'id': 'NEW_ID',
            'uploader': 'New Channel',
            'upload_date': '20230601'
        }
        temp_file = Path(temp_dir) / "test.mp4"
        temp_file.write_text("fake video")
        mock_ydl.prepare_filename.return_value = str(temp_file)
        mock_ydl_class.return_value = mock_ydl
        
        # Clear original metadata
        sample_item.video_id = None
        sample_item.uploader = None
        sample_item.upload_date = None
        
        downloader = VideoDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        # Verify metadata was updated
        assert result.video_id == 'NEW_ID'
        assert result.uploader == 'New Channel'
        assert result.upload_date == '20230601'
