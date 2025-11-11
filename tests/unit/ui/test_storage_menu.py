import pytest
from unittest.mock import patch, MagicMock
from storage_menu import StorageMenu
from managers.config_manager import StorageConfig
from pathlib import Path

# --- Fixtures and Mocks ---

@pytest.fixture
def mock_managers():
    """Mock required manager dependencies."""
    mock_config_manager = MagicMock()
    mock_storage_manager = MagicMock()
    
    # Mock config data
    mock_config_manager.config = MagicMock()
    mock_config_manager.config.default_storage = "local"
    mock_config_manager.config.storage_providers = {
        "ftp_backup": StorageConfig(enabled=True, provider_type="ftp", host="ftp.example.com").to_dict(),
        "gdrive_archive": StorageConfig(enabled=False, provider_type="gdrive").to_dict()
    }
    
    # Mock list_storage_providers to return keys
    mock_config_manager.list_storage_providers.return_value = [
        "ftp_backup", "gdrive_archive"
    ]
    
    # Mock get_storage_provider to return a StorageConfig object
    def get_storage_provider_mock(name):
        if name == "ftp_backup":
            return StorageConfig.from_dict(mock_config_manager.config.storage_providers["ftp_backup"])
        return StorageConfig.from_dict(mock_config_manager.config.storage_providers["gdrive_archive"])

    mock_config_manager.get_storage_provider.side_effect = get_storage_provider_mock
    
    return {
        "config_manager": mock_config_manager,
        "storage_manager": mock_storage_manager,
    }


@pytest.fixture
def mock_rich_io(monkeypatch):
    """Mocks all rich console printing and user input methods."""
    mock_console_print = MagicMock()
    mock_prompt_ask = MagicMock()
    mock_confirm_ask = MagicMock()
    mock_intprompt_ask = MagicMock()
    
    monkeypatch.setattr("storage_menu.console.print", mock_console_print)
    monkeypatch.setattr("storage_menu.Prompt.ask", mock_prompt_ask)
    monkeypatch.setattr("storage_menu.Confirm.ask", mock_confirm_ask)
    monkeypatch.setattr("storage_menu.IntPrompt.ask", mock_intprompt_ask)
    
    return {
        "print": mock_console_print,
        "prompt": mock_prompt_ask,
        "confirm": mock_confirm_ask,
        "intprompt": mock_intprompt_ask,
    }


# Mock the storage provider utilities for test_storage_connections
@pytest.fixture
def mock_storage_utils(monkeypatch):
    """Mocks the external storage provider classes."""
    mock_provider = MagicMock()
    mock_provider.connect.return_value = True
    mock_provider.disconnect.return_value = None
    
    mock_ftp = MagicMock(return_value=mock_provider)
    mock_sftp = MagicMock(return_value=mock_provider)
    mock_gdrive = MagicMock(return_value=mock_provider)
    mock_dropbox = MagicMock(return_value=mock_provider)
    mock_onedrive = MagicMock(return_value=mock_provider)
    
    monkeypatch.setattr("storage_menu.FTPStorage", mock_ftp)
    monkeypatch.setattr("storage_menu.SFTPStorage", mock_sftp)
    monkeypatch.setattr("storage_menu.GoogleDriveStorage", mock_gdrive)
    monkeypatch.setattr("storage_menu.DropboxStorage", mock_dropbox)
    monkeypatch.setattr("storage_menu.OneDriveStorage", mock_onedrive)
    
    return mock_provider


# --- Test display_storage_menu ---

def test_display_storage_menu_returns_user_choice(mock_rich_io, mock_managers):
    """Test that the menu returns the selected option."""
    expected_choice = "6"  # Configure storage provider
    mock_rich_io["prompt"].return_value = expected_choice
    
    choice = StorageMenu.display_storage_menu(**mock_managers)
    assert choice == expected_choice


def test_display_storage_menu_shows_current_state(mock_rich_io, mock_managers):
    """Test that the display reflects the default storage and provider count."""
    
    StorageMenu.display_storage_menu(**mock_managers)
    
    # Verify the status panel content is printed
    output = str(mock_rich_io["print"].call_args_list[1])
    assert "Default Storage: local" in output
    assert "Configured Providers: 2" in output


# --- Test add_ftp_storage ---

def test_add_ftp_storage_collects_input_and_calls_add(mock_rich_io, mock_managers):
    """Test gathering input for FTP and calling add_storage_provider."""
    
    # Simulate user input
    mock_rich_io["prompt"].side_effect = [
        "home_ftp",        # name
        "ftp.myhost.com",  # host
        "user1",           # username
        "mypass",          # password
        "/data",           # base_path
        "",                # video_quality (default)
        "128",             # audio_quality
    ]
    mock_rich_io["intprompt"].return_value = 21 # port
    
    StorageMenu.add_ftp_storage(mock_managers["config_manager"])
    
    # Assert add_storage_provider was called
    mock_managers["config_manager"].add_storage_provider.assert_called_once()
    name, config = mock_managers["config_manager"].add_storage_provider.call_args[0]
    
    assert name == "home_ftp"
    # Check key fields in the StorageConfig dict
    assert config.provider_type == "ftp"
    assert config.host == "ftp.myhost.com"
    assert config.audio_quality == "128"
    assert config.video_quality is None


# --- Test add_sftp_storage (Key Auth) ---

def test_add_sftp_storage_key_auth(mock_rich_io, mock_managers):
    """Test adding SFTP using key authentication."""
    
    # Simulate user input
    mock_rich_io["prompt"].side_effect = [
        "sftp_repo",
        "sftp.myhost.com",
        "ssh_user",
        "/home/user/.ssh/id_rsa", # key_filename
        "/backup",
        "720p",
        "",
    ]
    mock_rich_io["intprompt"].return_value = 22 # port
    mock_rich_io["confirm"].return_value = True # use_key = True
    
    StorageMenu.add_sftp_storage(mock_managers["config_manager"])
    
    # Assert add_storage_provider was called
    name, config = mock_managers["config_manager"].add_storage_provider.call_args[0]
    
    assert name == "sftp_repo"
    assert config.provider_type == "sftp"
    assert config.key_filename == "/home/user/.ssh/id_rsa"
    assert config.password == "" # Should be empty for key auth


# --- Test add_google_drive_storage ---

@patch("storage_menu.Path.exists", return_value=True)
def test_add_gdrive_storage(mock_exists, mock_rich_io, mock_managers):
    """Test adding Google Drive storage."""
    
    mock_rich_io["prompt"].side_effect = [
        "gdrive_main",
        "/path/to/creds.json", # credentials_file
        "folder_id_xyz",
        "", # video_quality
        "320", # audio_quality
    ]
    
    StorageMenu.add_google_drive_storage(mock_managers["config_manager"])
    
    name, config = mock_managers["config_manager"].add_storage_provider.call_args[0]
    
    assert name == "gdrive_main"
    assert config.provider_type == "gdrive"
    assert config.credentials_file == "/path/to/creds.json"
    assert config.folder_id == "folder_id_xyz"


# --- Test configure_storage_provider ---

def test_configure_storage_provider_updates_quality_and_status(mock_rich_io, mock_managers):
    """Test updating existing provider settings (enabled status and quality)."""
    
    # 1. User input: Select 'ftp_backup' (1)
    mock_rich_io["intprompt"].return_value = 1
    
    # 2. User input: Disable storage and change quality
    mock_rich_io["confirm"].return_value = False # Disable
    mock_rich_io["prompt"].side_effect = [
        "360p", # new video quality
        "",     # skip audio quality change (keep existing)
    ]
    
    # Execution
    StorageMenu.configure_storage_provider(mock_managers["config_manager"])
    
    # Retrieve the configuration that was *passed* back to config_manager.add_storage_provider
    name, updated_config = mock_managers["config_manager"].add_storage_provider.call_args[0]
    
    assert name == "ftp_backup"
    assert updated_config.enabled is False
    assert updated_config.video_quality == "360p"
    assert updated_config.audio_quality is None # Still None, as it was skipped in prompt


# --- Test remove_storage_provider ---

def test_remove_storage_provider_confirms_and_removes(mock_rich_io, mock_managers):
    """Test selecting and confirming removal of a provider."""
    
    # 1. User input: Select 'gdrive_archive' (2)
    mock_rich_io["intprompt"].return_value = 2
    
    # 2. User input: Confirm removal
    mock_rich_io["confirm"].return_value = True
    
    # Execution
    StorageMenu.remove_storage_provider(mock_managers["config_manager"])
    
    # Assertions
    mock_managers["config_manager"].remove_storage_provider.assert_called_once_with("gdrive_archive")


# --- Test set_default_storage ---

def test_set_default_storage(mock_rich_io, mock_managers):
    """Test setting a configured provider as the new default."""
    
    # Providers list is ["local", "ftp_backup", "gdrive_archive"]
    # 1. User input: Select 'ftp_backup' (2)
    mock_rich_io["intprompt"].return_value = 2
    
    # Execution
    StorageMenu.set_default_storage(mock_managers["config_manager"])
    
    # Assertions
    mock_managers["config_manager"].set_default_storage.assert_called_once_with("ftp_backup")


# --- Test test_storage_connections ---

def test_test_storage_connections_success(mock_rich_io, mock_managers, mock_storage_utils):
    """Test that connections are attempted and reported as successful."""
    
    # Execution
    StorageMenu.test_storage_connections(**mock_managers)
    
    # Assert connection was attempted for ftp_backup (which is enabled)
    mock_storage_utils.connect.assert_called_once()
    
    # Assert ftp_backup was marked as Connected
    output = str(mock_rich_io["print"].call_args_list[-1])
    assert "ftp_backup" in output
    assert "Connected" in output
    
    # Assert gdrive_archive was marked as Disabled (because enabled=False in fixture)
    assert "gdrive_archive" in output
    assert "Disabled" in output


def test_test_storage_connections_failure(mock_rich_io, mock_managers, mock_storage_utils):
    """Test that failed connections are correctly reported."""
    
    # Configure the mock provider to fail connection
    mock_storage_utils.connect.return_value = False
    
    # Execution
    StorageMenu.test_storage_connections(**mock_managers)
    
    # Assert failure status is reported
    output = str(mock_rich_io["print"].call_args_list[-1])
    assert "ftp_backup" in output
    assert "Failed" in output
