import pytest
from unittest.mock import patch, MagicMock
from progress_display import ProgressDisplay

# Mock the rich.progress.Progress class and its methods
@pytest.fixture
def mock_progress_class():
    """Mocks the rich.progress.Progress class."""
    mock_progress_instance = MagicMock()
    # Mock methods of the instance
    mock_progress_instance.start = MagicMock()
    mock_progress_instance.stop = MagicMock()
    mock_progress_instance.add_task = MagicMock(return_value=1) # Mock task ID
    mock_progress_instance.update = MagicMock()
    
    with patch("progress_display.Progress", return_value=mock_progress_instance) as mock_class:
        yield mock_progress_instance, mock_class


@pytest.fixture
def progress_display_instance():
    """Returns a fresh ProgressDisplay instance."""
    # Note: We need to ensure the Progress class mock is in place when this is instantiated
    return ProgressDisplay()


# --- Test Initialization and State Management ---

def test_init_sets_initial_state(progress_display_instance):
    """Test that __init__ correctly sets up initial state."""
    assert progress_display_instance.progress is None
    assert progress_display_instance.task_id is None


def test_create_simple_progress_sets_state(progress_display_instance, mock_progress_class):
    """Test that creating a progress bar starts the progress and sets task_id."""
    mock_instance, mock_class = mock_progress_class
    
    progress_display_instance.create_simple_progress("Test Task", total=200)
    
    # Assert state is set
    assert progress_display_instance.progress == mock_instance
    assert progress_display_instance.task_id == 1
    
    # Assert rich methods were called
    mock_instance.start.assert_called_once()
    mock_instance.add_task.assert_called_once()


def test_update_progress_updates_correctly(progress_display_instance, mock_progress_class):
    """Test that update_progress calls the mock rich update method."""
    mock_instance, _ = mock_progress_class
    
    progress_display_instance.create_simple_progress("Test Task", total=100)
    progress_display_instance.update_progress(50)
    
    mock_instance.update.assert_called_with(1, completed=50)


def test_complete_progress_stops_progress_and_clears_state(progress_display_instance, mock_progress_class):
    """Test that completing the progress bar stops the rich object and resets state."""
    mock_instance, _ = mock_progress_class
    
    progress_display_instance.create_simple_progress("Test Task", total=100)
    progress_display_instance.complete_progress()
    
    mock_instance.stop.assert_called_once()
    assert progress_display_instance.progress is None
    assert progress_display_instance.task_id is None


# --- Test yt-dlp Progress Hook ---

def test_yt_dlp_hook_updates_on_downloading_status(progress_display_instance, mock_progress_class):
    """Test that the hook calculates and updates percentage correctly."""
    mock_instance, _ = mock_progress_class
    
    progress_display_instance.create_simple_progress("Test Download", total=100) # Total is arbitrary here, actual total is from hook data
    hook = progress_display_instance.get_yt_dlp_progress_hook()
    
    # Simulate a mid-download state
    download_info = {
        'status': 'downloading',
        'downloaded_bytes': 50 * 1024 * 1024, # 50 MB
        'total_bytes': 100 * 1024 * 1024,     # 100 MB
        'filename': 'video.mp4'
    }
    
    hook(download_info)
    
    # Check if the update was called with 50% completion (100 * (50/100))
    mock_instance.update.assert_called_with(1, completed=50.0)


def test_yt_dlp_hook_updates_on_total_bytes_estimate(progress_display_instance, mock_progress_class):
    """Test that the hook uses total_bytes_estimate if total_bytes is missing."""
    mock_instance, _ = mock_progress_class
    progress_display_instance.create_simple_progress("Test Download", total=100)
    hook = progress_display_instance.get_yt_dlp_progress_hook()
    
    download_info = {
        'status': 'downloading',
        'downloaded_bytes': 20 * 1024,
        'total_bytes_estimate': 80 * 1024,
        'filename': 'video.mp4'
    }
    
    hook(download_info)
    
    # 20/80 = 25%
    mock_instance.update.assert_called_with(1, completed=25.0)


def test_yt_dlp_hook_updates_to_100_on_finished_status(progress_display_instance, mock_progress_class):
    """Test that the hook sets completed to 100% on 'finished' status."""
    mock_instance, _ = mock_progress_class
    
    progress_display_instance.create_simple_progress("Test Download", total=100)
    hook = progress_display_instance.get_yt_dlp_progress_hook()
    
    # Simulate finished state
    download_info = {
        'status': 'finished',
        'downloaded_bytes': 1000,
        'total_bytes': 1000,
        'filename': 'video.mp4'
    }
    
    hook(download_info)
    
    # Check if the update was called with 100 completion
    mock_instance.update.assert_called_with(1, completed=100)

def test_yt_dlp_hook_does_nothing_if_progress_is_none(progress_display_instance, mock_progress_class):
    """Test that the hook is safe to call even if progress bar is not active."""
    mock_instance, _ = mock_progress_class
    
    # Do NOT call create_simple_progress
    hook = progress_display_instance.get_yt_dlp_progress_hook()
    
    download_info = {'status': 'downloading', 'downloaded_bytes': 50, 'total_bytes': 100}
    hook(download_info)
    
    mock_instance.update.assert_not_called()
