import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

# To run these tests, you would normally ensure the original config_manager.py is 
# importable. We will use patching extensively to isolate the logic.

# Mocking the source data classes and the ConfigManager for test isolation.
# In a real environment, you would import them:
# from config_manager import StorageConfig, AppConfig, ConfigManager

# Mocking the rich console to suppress terminal output during tests
class MockConsole:
    def print(self, *args, **kwargs):
        pass

# --- Setup Fixtures ---

@pytest.fixture(scope="module", autouse=True)
def mock_rich_console():
    """Patches the rich console globally to prevent test output."""
    # Patch the console in the original module's namespace
    with patch('config_manager.console', MockConsole()):
        yield

@pytest.fixture
def mock_path_exists():
    """Fixture to mock Path.exists() for controlling file presence."""
    with patch('pathlib.Path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_open_json():
    """Fixture to mock the built-in open function and json operations."""
    m = mock_open()
    with patch('builtins.open', m) as mock_file:
        yield mock_file, m # Return the mock object and its handler

@pytest.fixture
def manager(mock_path_exists, mock_rich_console):
    """Provides a fresh ConfigManager instance for each test."""
    # Ensure config file does not exist by default for a clean slate
    mock_path_exists.return_value = False
    # Import the real ConfigManager for testing
    from config_manager import ConfigManager
    return ConfigManager(config_file="test_config.json")

# --- Test Data Class Serialization ---

def test_storage_config_serialization():
    from config_manager import StorageConfig
    config_data = {
        "enabled": True, 
        "provider_type": "sftp", 
        "host": "test.com", 
        "port": 22,
        "key_filename": "/path/to/key",
        "audio_quality": "320"
    }
    config_obj = StorageConfig.from_dict(config_data)
    
    assert config_obj.host == "test.com"
    assert config_obj.port == 22
    assert config_obj.audio_quality == "320"
    
    new_data = config_obj.to_dict()
    assert new_data["provider_type"] == "sftp"
    assert new_data["enabled"] == True
    # Ensure all original keys are present in the output
    assert len(new_data) == 16 

def test_app_config_serialization():
    from config_manager import AppConfig
    config_data = {
        "cookies_file": "/tmp/cookies.txt",
        "max_workers": 5,
        "default_storage": "gdrive_backup",
        "storage_providers": {"gdrive_backup": {"enabled": True, "provider_type": "gdrive"}},
        "setup_completed": True,
        "proxies": ["http://proxy.com"],
        "min_delay_seconds": 1.5,
        "alert_thresholds_mb": [500]
    }
    config_obj = AppConfig.from_dict(config_data)
    
    assert config_obj.max_workers == 5
    assert config_obj.default_storage == "gdrive_backup"
    assert config_obj.proxies == ["http://proxy.com"]
    
    new_data = config_obj.to_dict()
    assert new_data["min_delay_seconds"] == 1.5
    assert new_data["setup_completed"] == True


# --- Test ConfigManager Initialization and I/O ---

@patch('json.load')
def test_load_config_file_exists(mock_json_load, manager, mock_path_exists, mock_open_json):
    """Test loading a valid config file."""
    mock_path_exists.return_value = True
    # Mocking a basic dictionary that AppConfig can digest
    mock_json_load.return_value = {
        'cookies_file': '/test/cookies.txt', 
        'max_workers': 5, 
        'default_storage': 'local', 
        'storage_providers': {}, 
        'setup_completed': False,
        'proxies': [],
        'default_filename_template': "{index:03d} - {title}",
        'monitoring_enabled': False,
        'download_timeout_minutes': 120,
        'alert_thresholds_mb': [250, 1000, 5000, 10000],
        'max_downloads_per_hour': 50,
        'min_delay_seconds': 2.0,
        'max_delay_seconds': 5.0,
        'auto_record_live_streams': False,
        'wait_for_scheduled_streams': False,
        'max_stream_wait_minutes': 60,
        'default_video_quality': "720p",
        'default_audio_quality': "192",
        'normalize_filenames': True,
        'oauth_token': None,
        'oauth_refresh_token': None,
        'oauth_expiry': None,
        'slack_webhook_url': None,
        'bandwidth_limit_mbps': None,
    }

    config = manager.load_config()
    
    assert config.max_workers == 5
    assert config.cookies_file == '/test/cookies.txt'
    mock_open_json[1].assert_called_once_with(Path("test_config.json"), 'r', encoding='utf-8')
    mock_json_load.assert_called_once()


def test_load_config_file_missing(manager, mock_path_exists):
    """Test loading when no config file is present (should return defaults)."""
    mock_path_exists.return_value = False
    config = manager.load_config()
    
    assert config.max_workers == 3  # Default value
    assert config.default_storage == "local"
    # Ensure the correct type is returned
    from config_manager import AppConfig
    assert isinstance(config, AppConfig)


@patch('json.load')
def test_load_config_file_corrupt(mock_json_load, manager, mock_path_exists, mock_open_json):
    """Test corrupted file loading (should fall back to default config)."""
    mock_path_exists.return_value = True
    # Simulate JSONDecodeError or other file read error
    mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

    config = manager.load_config()
    
    # Should fall back to default config
    assert config.max_workers == 3
    from config_manager import AppConfig
    assert isinstance(config, AppConfig)


@patch('json.dump')
def test_save_config(mock_json_dump, manager, mock_open_json):
    """Test saving config ensures data is dumped to the correct file."""
    # Modify config
    manager.config.max_workers = 10
    manager.save_config()

    # Verify that open and json.dump were called correctly
    mock_open_json[1].assert_called_once_with(Path("test_config.json"), 'w', encoding='utf-8')
    mock_json_dump.assert_called_once()
    
    # Check that max_workers was included in the data dumped
    dump_args, _ = mock_json_dump.call_args
    dumped_data = dump_args[0]
    assert dumped_data['max_workers'] == 10


# --- Test Storage Provider Management (CRUD) ---

def test_storage_provider_management(manager, mock_open_json):
    from config_manager import StorageConfig
    
    # Setup: Create a mock storage config object
    mock_storage = StorageConfig(
        enabled=True, 
        provider_type="sftp", 
        host="sftp.example.com"
    )
    mock_storage_2 = StorageConfig(
        enabled=False, 
        provider_type="gdrive", 
        folder_id="12345"
    )

    # 1. Add providers
    manager.add_storage_provider("sftp_backup", mock_storage)
    manager.add_storage_provider("gdrive_cloud", mock_storage_2)
    assert "sftp_backup" in manager.config.storage_providers
    assert manager.config.storage_providers["gdrive_cloud"]["folder_id"] == "12345"

    # 2. List providers
    assert sorted(manager.list_storage_providers()) == ["gdrive_cloud", "sftp_backup"]

    # 3. Get provider
    retrieved_config = manager.get_storage_provider("sftp_backup")
    assert isinstance(retrieved_config, StorageConfig)
    assert retrieved_config.host == "sftp.example.com"
    
    # Get non-existent provider
    assert manager.get_storage_provider("missing") is None

    # 4. Set default storage
    manager.set_default_storage("gdrive_cloud")
    assert manager.config.default_storage == "gdrive_cloud"
    manager.set_default_storage("local")
    assert manager.config.default_storage == "local"
    
    # Try to set default to non-existent provider (should be ignored)
    manager.set_default_storage("not_a_provider")
    assert manager.config.default_storage == "local"

    # 5. Remove provider (non-default)
    manager.remove_storage_provider("sftp_backup")
    assert "sftp_backup" not in manager.config.storage_providers
    assert manager.config.default_storage == "local" # Default should be unchanged

    # 6. Remove provider (was default)
    manager.set_default_storage("gdrive_cloud")
    manager.remove_storage_provider("gdrive_cloud")
    assert "gdrive_cloud" not in manager.config.storage_providers
    assert manager.config.default_storage == "local" # Should reset default
