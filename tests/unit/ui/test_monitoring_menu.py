import pytest
from unittest.mock import patch, MagicMock
from monitoring_menu import MonitoringMenu
from models.channel import Channel
from enums import DownloadFormat
from datetime import datetime
from pathlib import Path

# --- Fixtures and Mocks ---

@pytest.fixture
def mock_managers():
    """Mock required manager dependencies."""
    mock_monitor_manager = MagicMock()
    mock_downloader = MagicMock()
    mock_queue_manager = MagicMock()
    mock_config_manager = MagicMock()
    mock_slack_notifier = MagicMock()

    # Default monitored channels list
    mock_channel_monitored = Channel(
        id=1, url="http://channel1.com", title="Monitored Channel 1", is_monitored=True,
        check_interval_minutes=30, last_checked=datetime.now().isoformat(), enabled=True,
        format_type=DownloadFormat.VIDEO.value
    )
    mock_channel_unmonitored = Channel(
        id=2, url="http://channel2.com", title="Unmonitored Channel 2", is_monitored=False
    )
    
    mock_monitor_manager.is_running = False
    mock_monitor_manager.get_all_channels.return_value = [
        mock_channel_monitored, mock_channel_unmonitored
    ]
    mock_monitor_manager.get_channel_by_url.return_value = None

    mock_config_manager.config = MagicMock()
    mock_config_manager.config.default_filename_template = "{index} - {title}"

    return {
        "monitor": mock_monitor_manager,
        "downloader": mock_downloader,
        "queue": mock_queue_manager,
        "config": mock_config_manager,
        "slack": mock_slack_notifier,
        "monitored_channel": mock_channel_monitored,
    }


@pytest.fixture
def mock_rich_io(monkeypatch):
    """Mocks all rich console printing and user input methods."""
    mock_console_print = MagicMock()
    mock_prompt_ask = MagicMock()
    mock_confirm_ask = MagicMock()
    mock_intprompt_ask = MagicMock()

    monkeypatch.setattr("monitoring_menu.console.print", mock_console_print)
    monkeypatch.setattr("monitoring_menu.Prompt.ask", mock_prompt_ask)
    monkeypatch.setattr("monitoring_menu.Confirm.ask", mock_confirm_ask)
    monkeypatch.setattr("monitoring_menu.IntPrompt.ask", mock_intprompt_ask)

    return {
        "print": mock_console_print,
        "prompt": mock_prompt_ask,
        "confirm": mock_confirm_ask,
        "intprompt": mock_intprompt_ask,
    }


# --- Test display_monitoring_menu ---

def test_display_monitoring_menu_returns_user_choice(mock_rich_io, mock_managers):
    """Test that the menu returns the selected option."""
    expected_choice = "3"  # Start monitoring
    mock_rich_io["prompt"].return_value = expected_choice

    choice = MonitoringMenu.display_monitoring_menu(**mock_managers)
    assert choice == expected_choice


def test_display_monitoring_menu_shows_running_status(mock_rich_io, mock_managers):
    """Test that the status panel correctly reflects running state."""
    mock_managers["monitor"].is_running = True
    
    MonitoringMenu.display_monitoring_menu(**mock_managers)
    
    # Check that 'Running' status text is generated
    assert "Running" in str(mock_rich_io["print"].call_args_list[1]) # Status panel content


def test_display_monitoring_menu_lists_monitored_channels(mock_rich_io, mock_managers):
    """Test that the monitored channels table is printed."""
    MonitoringMenu.display_monitoring_menu(**mock_managers)

    # The console.print calls for the Table object should contain the channel title
    table_content = [str(call) for call in mock_rich_io["print"].call_args_list if "Monitored Channel 1" in str(call)]
    assert len(table_content) > 0


# --- Test add_channel_to_monitoring (New Channel) ---

@patch("monitoring_menu.Path.mkdir")
@patch("monitoring_menu.Path.exists", return_value=True) # Mock Path.exists for simplicity
def test_add_channel_inserts_new_channel(mock_exists, mock_mkdir, mock_rich_io, mock_managers):
    """Test adding a completely new channel to monitoring."""
    
    # 1. Mock downloader.get_playlist_info result
    mock_managers["downloader"].get_playlist_info.return_value = {
        'title': 'New Test Playlist',
        'channel_url': 'http://channel_new.com',
        'uploader': 'New Uploader',
    }
    
    # 2. Mock user input for quality, directory, interval, template, and order
    mock_rich_io["prompt"].side_effect = [
        "http://new.playlist.com",      # playlist_url
        "video",                        # format_choice
        "1",                            # quality_choice (best)
        "downloads/new_test_playlist",  # output_dir
        "1",                            # download_order (original)
    ]
    mock_rich_io["intprompt"].return_value = 45 # interval
    mock_rich_io["confirm"].return_value = True # use_template
    
    # 3. Execution
    with patch.object(MonitoringMenu, '_get_quality_choice', return_value='best'):
        with patch.object(MonitoringMenu, '_get_download_order', return_value='original'):
            MonitoringMenu.add_channel_to_monitoring(**mock_managers)

    # 4. Assertions
    mock_managers["monitor"].get_channel_by_url.assert_called_with('http://channel_new.com')
    mock_managers["monitor"].add_channel.assert_called_once()
    
    # Check that the inserted channel is correct
    channel_added = mock_managers["monitor"].add_channel.call_args[0][0]
    assert channel_added.url == 'http://channel_new.com'
    assert channel_added.is_monitored is True
    assert channel_added.check_interval_minutes == 45
    assert channel_added.quality == 'best'


# --- Test add_channel_to_monitoring (Existing Channel) ---

@patch("monitoring_menu.Path.mkdir")
def test_add_channel_updates_existing_channel(mock_mkdir, mock_rich_io, mock_managers):
    """Test updating an existing channel to turn on monitoring."""
    
    # Set up mock existing channel
    existing_channel = Channel(
        id=99, url="http://existing.com", title="Old Title", is_monitored=False,
        quality="480p", format_type="audio"
    )
    mock_managers["monitor"].get_channel_by_url.return_value = existing_channel

    # Mock playlist info that matches the existing channel's URL (channel_url)
    mock_managers["downloader"].get_playlist_info.return_value = {
        'title': 'New Playlist Title',
        'channel_url': 'http://existing.com',
        'uploader': 'New Uploader',
    }
    
    # Mock user input
    mock_rich_io["prompt"].side_effect = [
        "http://existing.com/playlist",  # playlist_url
        "video",                         # format_choice (change from audio)
        "1",                             # quality_choice (best)
        "downloads/new_dir",             # output_dir
        "2",                             # download_order (oldest_first)
    ]
    mock_rich_io["intprompt"].return_value = 15 # interval
    mock_rich_io["confirm"].return_value = False # don't use template

    # Execution
    with patch.object(MonitoringMenu, '_get_quality_choice', return_value='best'):
        with patch.object(MonitoringMenu, '_get_download_order', return_value='oldest_first'):
            MonitoringMenu.add_channel_to_monitoring(**mock_managers)

    # Assertions
    mock_managers["monitor"].update_channel.assert_called_once()
    
    # Verify that the existing channel object was updated in place
    assert existing_channel.is_monitored is True
    assert existing_channel.check_interval_minutes == 15
    assert existing_channel.format_type == "video"
    assert existing_channel.quality == "best"
    assert existing_channel.filename_template is None


# --- Test remove_channel_from_monitoring ---

def test_remove_channel_updates_monitoring_status(mock_rich_io, mock_managers):
    """Test that removing a channel sets its is_monitored flag to False."""
    
    # Mock user input to select the first monitored channel (index 1)
    mock_rich_io["intprompt"].return_value = 1
    
    # Execution
    MonitoringMenu.remove_channel_from_monitoring(mock_managers["monitor"])
    
    # Assertions
    mock_channel = mock_managers["monitored_channel"]
    
    # The channel object should be updated
    assert mock_channel.is_monitored is False
    
    # The update method should be called on the manager
    mock_managers["monitor"].update_channel.assert_called_once_with(mock_channel)


def test_remove_channel_skips_on_no_monitored_channels(mock_rich_io, mock_managers):
    """Test that removal is skipped gracefully if no channels are monitored."""
    
    # Set all channels to unmonitored
    mock_managers["monitor"].get_all_channels.return_value = [
        Channel(id=1, url="u1", title="C1", is_monitored=False)
    ]
    
    # Execution
    MonitoringMenu.remove_channel_from_monitoring(mock_managers["monitor"])
    
    # Assertions
    mock_managers["monitor"].update_channel.assert_not_called()
    assert "No monitored channels" in str(mock_rich_io["print"].call_args_list[-1])


# --- Test _get_quality_choice ---

def test_get_quality_choice_returns_audio_default(mock_rich_io):
    """Test that audio format returns '192' immediately."""
    result = MonitoringMenu._get_quality_choice(DownloadFormat.AUDIO.value)
    assert result == "192"
    assert mock_rich_io["prompt"].call_count == 0


def test_get_quality_choice_returns_video_choice(mock_rich_io):
    """Test that video format prompts the user and returns the correct quality string."""
    # User selects option 4 (480p)
    mock_rich_io["prompt"].return_value = "4"
    
    result = MonitoringMenu._get_quality_choice(DownloadFormat.VIDEO.value)
    
    assert result == "480p"
    mock_rich_io["prompt"].assert_called_once()


# --- Test _get_download_order ---

def test_get_download_order_returns_correct_choice(mock_rich_io):
    """Test that download order prompt returns the correct value."""
    # User selects option 3 (newest_first)
    mock_rich_io["prompt"].return_value = "3"
    
    result = MonitoringMenu._get_download_order()
    
    assert result == "newest_first"
    mock_rich_io["prompt"].assert_called_once()
