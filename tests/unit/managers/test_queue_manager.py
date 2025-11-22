"""Tests for QueueManager"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from managers.queue_manager import QueueManager
from models.queue import Queue
from models.download_item import DownloadItem
from enums import DownloadStatus


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield str(db_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def queue_manager(temp_db):
    """Create QueueManager with temp database"""
    return QueueManager(db_path=temp_db)


@pytest.fixture
def sample_queue():
    """Create sample queue for testing"""
    return Queue(
        id=None,
        playlist_url="https://www.youtube.com/playlist?list=TEST123",
        playlist_title="Test Playlist",
        format_type="video",
        quality="720p",
        output_dir="downloads/test",
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
        id=None,
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


class TestQueueManager:
    """Test QueueManager functionality"""
    
    def test_init_creates_database(self, temp_db):
        """Test database initialization"""
        manager = QueueManager(db_path=temp_db)
        assert Path(temp_db).exists()
    
    def test_create_queue_success(self, queue_manager, sample_queue):
        """Test creating a queue"""
        queue_id = queue_manager.create_queue(sample_queue)
        assert queue_id > 0
        assert isinstance(queue_id, int)
    
    def test_get_queue_by_id(self, queue_manager, sample_queue):
        """Test retrieving queue by ID"""
        queue_id = queue_manager.create_queue(sample_queue)
        retrieved = queue_manager.get_queue(queue_id)
        
        assert retrieved is not None
        assert retrieved.id == queue_id
        assert retrieved.playlist_title == "Test Playlist"
        assert retrieved.format_type == "video"
        assert retrieved.quality == "720p"
    
    def test_get_queue_nonexistent(self, queue_manager):
        """Test getting non-existent queue returns None"""
        result = queue_manager.get_queue(99999)
        assert result is None
    
    def test_get_all_queues_empty(self, queue_manager):
        """Test getting all queues when none exist"""
        queues = queue_manager.get_all_queues()
        assert queues == []
    
    def test_get_all_queues(self, queue_manager, sample_queue):
        """Test getting all queues"""
        queue_manager.create_queue(sample_queue)
        queue_manager.create_queue(sample_queue)
        
        queues = queue_manager.get_all_queues()
        assert len(queues) == 2
    
    def test_update_queue(self, queue_manager, sample_queue):
        """Test updating a queue"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_queue.id = queue_id
        sample_queue.status = "completed"
        sample_queue.completed_at = datetime.now().isoformat()
        
        queue_manager.update_queue(sample_queue)
        updated = queue_manager.get_queue(queue_id)
        
        assert updated.status == "completed"
        assert updated.completed_at is not None
    
    def test_delete_queue(self, queue_manager, sample_queue):
        """Test deleting a queue"""
        queue_id = queue_manager.create_queue(sample_queue)
        queue_manager.delete_queue(queue_id)
        
        result = queue_manager.get_queue(queue_id)
        assert result is None
    
    def test_add_item_to_queue(self, queue_manager, sample_queue, sample_item):
        """Test adding item to queue"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_item.queue_id = queue_id
        
        item_id = queue_manager.add_item(sample_item)
        assert item_id > 0
    
    def test_get_queue_items(self, queue_manager, sample_queue, sample_item):
        """Test getting items for a queue"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_item.queue_id = queue_id
        
        queue_manager.add_item(sample_item)
        queue_manager.add_item(sample_item)
        
        items = queue_manager.get_queue_items(queue_id)
        assert len(items) == 2
    
    def test_update_item(self, queue_manager, sample_queue, sample_item):
        """Test updating a download item"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_item.queue_id = queue_id
        item_id = queue_manager.add_item(sample_item)
        
        sample_item.id = item_id
        sample_item.status = DownloadStatus.COMPLETED.value
        sample_item.file_size_bytes = 1024000
        
        queue_manager.update_item(sample_item)
        updated = queue_manager.get_item(item_id)
        
        assert updated.status == DownloadStatus.COMPLETED.value
        assert updated.file_size_bytes == 1024000
    
    def test_get_queue_stats(self, queue_manager, sample_queue, sample_item):
        """Test getting queue statistics"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_item.queue_id = queue_id
        
        # Add 3 items with different statuses
        sample_item.status = DownloadStatus.COMPLETED.value
        sample_item.file_size_bytes = 1024000
        queue_manager.add_item(sample_item)
        
        sample_item.status = DownloadStatus.PENDING.value
        queue_manager.add_item(sample_item)
        
        sample_item.status = DownloadStatus.FAILED.value
        queue_manager.add_item(sample_item)
        
        stats = queue_manager.get_queue_stats(queue_id)
        
        assert stats['total'] == 3
        assert stats['completed'] == 1
        assert stats['pending'] == 1
        assert stats['failed'] == 1
        assert stats['total_size_mb'] > 0
    
    def test_record_queue_interruption(self, queue_manager, sample_queue, sample_item):
        """Test recording queue interruption"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_item.queue_id = queue_id
        sample_item.status = DownloadStatus.PENDING.value
        queue_manager.add_item(sample_item)
        queue_manager.add_item(sample_item)
        
        queue_manager.record_queue_interruption(queue_id)
        
        resumable = queue_manager.get_resumable_queues()
        assert len(resumable) == 1
        assert resumable[0]['queue_id'] == queue_id
        assert resumable[0]['pending_count'] == 2
    
    def test_get_resumable_queues_empty(self, queue_manager):
        """Test getting resumable queues when none exist"""
        resumable = queue_manager.get_resumable_queues()
        assert resumable == []
    
    def test_clear_queue_resume(self, queue_manager, sample_queue, sample_item):
        """Test clearing queue resume data"""
        queue_id = queue_manager.create_queue(sample_queue)
        sample_item.queue_id = queue_id
        sample_item.status = DownloadStatus.PENDING.value
        queue_manager.add_item(sample_item)
        
        queue_manager.record_queue_interruption(queue_id)
        assert len(queue_manager.get_resumable_queues()) == 1
        
        queue_manager.clear_queue_resume(queue_id)
        assert len(queue_manager.get_resumable_queues()) == 0
    
    def test_clear_all_resume_data(self, queue_manager, sample_queue, sample_item):
        """Test clearing all resume data"""
        queue_id1 = queue_manager.create_queue(sample_queue)
        queue_id2 = queue_manager.create_queue(sample_queue)
        
        sample_item.queue_id = queue_id1
        sample_item.status = DownloadStatus.PENDING.value
        queue_manager.add_item(sample_item)
        
        sample_item.queue_id = queue_id2
        queue_manager.add_item(sample_item)
        
        queue_manager.record_queue_interruption(queue_id1)
        queue_manager.record_queue_interruption(queue_id2)
        
        assert len(queue_manager.get_resumable_queues()) == 2
        
        queue_manager.clear_all_resume_data()
        assert len(queue_manager.get_resumable_queues()) == 0
