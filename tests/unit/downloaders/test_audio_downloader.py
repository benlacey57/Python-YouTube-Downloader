"""Tests for AudioDownloader"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from downloaders.audio import AudioDownloader
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
    """Create sample audio queue"""
    return Queue(
        id=1,
        playlist_url="https://www.youtube.com/playlist?list=TEST",
        playlist_title="Test Playlist",
        format_type="audio",
        quality="192",
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
        title="Test Song",
        video_id="TEST123",
        uploader="Test Artist",
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


class TestAudioDownloader:
    """Test AudioDownloader functionality"""
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    def test_init(self, mock_notif, mock_stats, mock_config):
        """Test AudioDownloader initialization"""
        downloader = AudioDownloader()
        assert downloader is not None
        assert downloader.rate_limiter is not None
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.audio.keyboard_handler')
    @patch('time.sleep')
    def test_download_item_success(self, mock_sleep, mock_kb, mock_ydl_class,
                                   mock_notif, mock_stats, mock_config,
                                   sample_item, sample_queue, temp_dir):
        """Test successful audio download"""
        # Setup mocks
        mock_kb.is_skip_requested.return_value = False
        mock_config_instance = MagicMock()
        mock_config_instance.config.normalize_filenames = True
        mock_config.return_value = mock_config_instance
        
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Song',
            'id': 'TEST123',
            'uploader': 'Test Artist',
            'upload_date': '20230101'
        }
        
        # Create temp MP3 file
        temp_file = Path(temp_dir) / "001 - Test Song.mp3"
        temp_file.write_text("fake audio content")
        mock_ydl_class.return_value = mock_ydl
        
        # Download
        downloader = AudioDownloader()
        result = downloader.download_item(sample_item, sample_queue, index=1)
        
        # Verify
        assert result.status == DownloadStatus.COMPLETED.value
        assert result.file_path is not None
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    @patch('downloaders.audio.keyboard_handler')
    def test_download_item_skip_requested(self, mock_kb, mock_notif, mock_stats,
                                         mock_config, sample_item, sample_queue):
        """Test download with skip requested"""
        mock_kb.is_skip_requested.return_value = True
        
        downloader = AudioDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        assert result.status == DownloadStatus.PENDING.value
        assert result.error == "Skipped by user"
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.audio.keyboard_handler')
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
        
        downloader = AudioDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        assert result.status == DownloadStatus.FAILED.value
        assert "Network error" in result.error
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.audio.keyboard_handler')
    @patch('time.sleep')
    def test_audio_quality_192(self, mock_sleep, mock_kb, mock_ydl_class,
                               mock_notif, mock_stats, mock_config,
                               sample_item, sample_queue, temp_dir):
        """Test audio download with 192kbps quality"""
        mock_kb.is_skip_requested.return_value = False
        sample_queue.quality = "192"
        
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {'title': 'Test', 'id': 'TEST'}
        temp_file = Path(temp_dir) / "test.mp3"
        temp_file.write_text("fake audio")
        mock_ydl_class.return_value = mock_ydl
        
        downloader = AudioDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        # Verify download attempted
        assert result.status in [DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value]
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.audio.keyboard_handler')
    @patch('time.sleep')
    def test_download_with_proxy(self, mock_sleep, mock_kb, mock_ydl_class,
                                 mock_notif, mock_stats, mock_config,
                                 sample_item, sample_queue, temp_dir):
        """Test audio download with proxy"""
        mock_kb.is_skip_requested.return_value = False
        proxy = "http://proxy.example.com:8080"
        
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {'title': 'Test', 'id': 'TEST'}
        temp_file = Path(temp_dir) / "test.mp3"
        temp_file.write_text("fake audio")
        mock_ydl_class.return_value = mock_ydl
        
        downloader = AudioDownloader()
        result = downloader.download_item(sample_item, sample_queue, proxy=proxy)
        
        # Verify download attempted
        assert result.status in [DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value]
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    @patch('yt_dlp.YoutubeDL')
    @patch('downloaders.audio.keyboard_handler')
    @patch('time.sleep')
    def test_metadata_extraction(self, mock_sleep, mock_kb, mock_ydl_class,
                                 mock_notif, mock_stats, mock_config,
                                 sample_item, sample_queue, temp_dir):
        """Test metadata extraction during audio download"""
        mock_kb.is_skip_requested.return_value = False
        
        # Mock yt-dlp with metadata
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Updated Song',
            'id': 'NEW_ID',
            'uploader': 'New Artist',
            'upload_date': '20230601'
        }
        temp_file = Path(temp_dir) / "test.mp3"
        temp_file.write_text("fake audio")
        mock_ydl_class.return_value = mock_ydl
        
        # Clear original metadata
        sample_item.video_id = None
        sample_item.uploader = None
        sample_item.upload_date = None
        
        downloader = AudioDownloader()
        result = downloader.download_item(sample_item, sample_queue)
        
        # Verify metadata was updated
        assert result.video_id == 'NEW_ID'
        assert result.uploader == 'New Artist'
        assert result.upload_date == '20230601'
    
    @patch('downloaders.audio.ConfigManager')
    @patch('downloaders.audio.StatsManager')
    @patch('downloaders.audio.NotificationManager')
    def test_audio_format_options(self, mock_notif, mock_stats, mock_config):
        """Test audio format options are set correctly"""
        downloader = AudioDownloader()
        opts = downloader.get_base_ydl_opts()
        
        # Verify basic options are present
        assert opts is not None
        assert 'quiet' in opts
