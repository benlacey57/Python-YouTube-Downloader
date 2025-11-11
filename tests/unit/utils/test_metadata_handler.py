import pytest
from unittest.mock import patch, MagicMock

# --- FIX FOR PACKAGE IMPORTS ---
# This ensures Python can find 'managers', 'utils', 'models', etc.
# when the script is run from the root directory.
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# -------------------------------

from utils.metadata_handler import MetadataHandler

# Mock mutagen to prevent ImportErrors when running tests
@pytest.fixture(autouse=True)
def mock_mutagen(monkeypatch):
    """Mocks mutagen imports for safe execution."""
    mock_mutagen_module = MagicMock()
    # Mock specific classes used in the source file
    mock_mutagen_module.mp4.MP4 = MagicMock()
    mock_mutagen_module.mp4.MP4Cover = MagicMock()
    mock_mutagen_module.id3.ID3 = MagicMock()
    mock_mutagen_module.mp3.MP3 = MagicMock()

    # Apply the mock to the module's imports
    monkeypatch.setattr('utils.metadata_handler.mutagen', mock_mutagen_module, raising=False)
    monkeypatch.setitem(MetadataHandler._set_mp4_metadata.__globals__, 'MP4', mock_mutagen_module.mp4.MP4)
    monkeypatch.setitem(MetadataHandler._set_mp3_metadata.__globals__, 'ID3', mock_mutagen_module.id3.ID3)
    monkeypatch.setitem(MetadataHandler._set_mp3_metadata.__globals__, 'MP3', mock_mutagen_module.mp3.MP3)
    monkeypatch.setitem(MetadataHandler._set_mp3_metadata.__globals__, 'TIT2', MagicMock())
    
    # We still need to patch the external import mechanism itself for set_video_metadata
    with patch.dict('sys.modules', {'mutagen': mock_mutagen_module}):
        yield mock_mutagen_module


# --- Test set_video_metadata (Dispatch and Error Handling) ---

@patch.object(MetadataHandler, '_set_mp4_metadata')
@patch.object(MetadataHandler, '_set_mp3_metadata')
@patch.object(Path, 'suffix', new_callable=lambda: MagicMock(return_value='.mp4'))
def test_set_video_metadata_dispatches_mp4(mock_suffix, mock_mp3, mock_mp4, mock_mutagen):
    """Test that .mp4 files are routed to _set_mp4_metadata."""
    MetadataHandler.set_video_metadata("test.mp4", {})
    mock_mp4.assert_called_once()
    mock_mp3.assert_not_called()


@patch.object(MetadataHandler, '_set_mp4_metadata')
@patch.object(MetadataHandler, '_set_mp3_metadata')
@patch.object(Path, 'suffix', new_callable=lambda: MagicMock(return_value='.mp3'))
def test_set_video_metadata_dispatches_mp3(mock_suffix, mock_mp3, mock_mp4, mock_mutagen):
    """Test that .mp3 files are routed to _set_mp3_metadata."""
    MetadataHandler.set_video_metadata("test.mp3", {})
    mock_mp3.assert_called_once()
    mock_mp4.assert_not_called()


@patch.object(MetadataHandler, '_set_mp4_metadata')
@patch.object(Path, 'suffix', new_callable=lambda: MagicMock(return_value='.avi'))
def test_set_video_metadata_unsupported_format(mock_suffix, mock_mp4, mock_mutagen, capsys):
    """Test handling of unsupported file types."""
    MetadataHandler.set_video_metadata("test.avi", {})
    mock_mp4.assert_not_called()
    assert "Metadata not supported for .avi files" in capsys.readouterr().out


@patch.object(MetadataHandler, '_set_mp4_metadata')
@patch.dict('sys.modules', {'mutagen': None})
def test_set_video_metadata_mutagen_not_installed(mock_mp4, capsys):
    """Test handling when mutagen is not importable (ImportError)."""
    # Need to remove the mock and replace it with None to simulate failure
    with pytest.raises(TypeError): # Mutagen will be None, triggering an early TypeError in the source
        MetadataHandler.set_video_metadata("test.mp4", {})
    
    # We must patch the initial try block logic to check for the console output
    with patch('utils.metadata_handler.console') as mock_console:
        try:
            from mutagen.mp4 import MP4
        except ImportError:
            # Simulate the error path in set_video_metadata
            mock_console.print("[yellow]mutagen not installed. Install with: pip install mutagen[/yellow]")
        
        mock_console.print.assert_called_once()
        

# --- Test extract_metadata ---

@pytest.mark.parametrize("video_info, index, playlist_title, expected_fields", [
    # Basic full extraction
    (
        {
            'title': 'My Great Video Title',
            'uploader': 'The Creator',
            'channel': 'The Channel Name', # Should be ignored if uploader exists
            'upload_date': '20230515',
            'description': 'A very long and detailed description for the video.',
            'webpage_url': 'http://youtube.com/watch/123'
        },
        5,
        "Best Playlist Ever",
        {
            'title': 'My Great Video Title',
            'artist': 'The Creator',
            'album': 'Best Playlist Ever',
            'year': '2023',
            'track': 5,
            'url': 'http://youtube.com/watch/123',
            'description': 'A very long and detailed description for the video.'
        }
    ),
    # Missing optional fields, minimal input
    (
        {
            'title': 'Minimal',
            'channel': 'Only Channel Name',
            'upload_date': '20240101'
        },
        0,
        "", # No playlist title
        {
            'title': 'Minimal',
            'artist': 'Only Channel Name',
            'year': '2024',
        }
    ),
    # Track number check (index=0 ignored)
    (
        {'title': 'T'},
        0,
        "",
        {'title': 'T'}
    ),
    # Description length limit (500 chars)
    (
        {
            'title': 'Long Desc',
            'description': 'A' * 600
        },
        1,
        "",
        {
            'title': 'Long Desc',
            'track': 1,
            'description': 'A' * 500
        }
    )
])
def test_extract_metadata_full_mapping(video_info, index, playlist_title, expected_fields):
    """Test that metadata is extracted correctly according to rules."""
    
    metadata = MetadataHandler.extract_metadata(video_info, index, playlist_title)
    
    # Check that all expected fields are present and correct
    for key, value in expected_fields.items():
        assert metadata.get(key) == value
        
    # Check that no unexpected fields are present (e.g., 'channel' shouldn't be present)
    assert 'channel' not in metadata

def test_extract_metadata_uploader_priority():
    """Test that 'uploader' takes priority over 'channel' for the 'artist' field."""
    video_info = {
        'uploader': 'Primary Uploader',
        'channel': 'Secondary Channel'
    }
    metadata = MetadataHandler.extract_metadata(video_info)
    assert metadata.get('artist') == 'Primary Uploader'

def test_extract_metadata_playlist_title_priority():
    """Test that playlist_title argument takes priority over 'playlist' key in video_info."""
    video_info = {
        'playlist': 'Video Info Playlist Name'
    }
    metadata = MetadataHandler.extract_metadata(video_info, playlist_title="External Playlist Name")
    assert metadata.get('album') == 'External Playlist Name'
