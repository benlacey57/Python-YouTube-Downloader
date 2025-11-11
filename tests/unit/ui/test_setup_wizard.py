import pytest
from unittest.mock import patch, MagicMock
from setup_wizard import SetupWizard
from managers.config_manager import AppConfig

# Mocking the rich components used for input and output
@pytest.fixture
def mock_rich_io(monkeypatch):
    """Mocks all rich console printing and user input methods."""
    mock_console_print = MagicMock()
    mock_confirm_ask = MagicMock()
    mock_prompt_ask = MagicMock()
    mock_intprompt_ask = MagicMock()
    
    monkeypatch.setattr("setup_wizard.console.print", mock_console_print)
    monkeypatch.setattr("setup_wizard.Confirm.ask", mock_confirm_ask)
    monkeypatch.setattr("setup_wizard.Prompt.ask", mock_prompt_ask)
    monkeypatch.setattr("setup_wizard.IntPrompt.ask", mock_intprompt_ask)
    
    # Mocking input() at the end of the wizard
    monkeypatch.setattr("builtins.input", MagicMock())
    
    return {
        "print": mock_console_print,
        "confirm": mock_confirm_ask,
        "prompt": mock_prompt_ask,
        "intprompt": mock_intprompt_ask,
    }

# Mock the Path.exists() for authentication setup
@pytest.fixture
def mock_path_exists(monkeypatch):
    mock_exists = MagicMock(return_value=True)
    monkeypatch.setattr("pathlib.Path.exists", mock_exists)
    return mock_exists


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager with a real AppConfig instance for state tracking."""
    mock_cm = MagicMock()
    # Ensure config object is a real AppConfig so attribute changes are tracked
    mock_cm.config = AppConfig()
    mock_cm.config.setup_completed = False
    mock_cm.config.default_filename_template = "{index:03d} - {title}"
    
    # Mock storage_providers property access
    mock_cm.config.storage_providers = {}
    return mock_cm


# --- Test run() method ---

def test_run_wizard_skips_if_user_confirms_skip(mock_rich_io, mock_config_manager):
    """Test that the wizard exits early if the user selects 'No' to run setup."""
    mock_rich_io["confirm"].return_value = False  # Skip setup
    
    SetupWizard.run(mock_config_manager)
    
    # Assert setup_completed is set to True
    assert mock_config_manager.config.setup_completed is True
    # Assert save_config was called immediately
    mock_config_manager.save_config.assert_called_once()
    
    # Assert no other setup steps were called
    assert mock_rich_io["prompt"].call_count == 1 # Only the first Confirm.ask is called implicitly


@patch.object(SetupWizard, '_show_summary')
@patch.object(SetupWizard, '_setup_notifications')
@patch.object(SetupWizard, '_setup_storage')
@patch.object(SetupWizard, '_setup_rate_limiting')
@patch.object(SetupWizard, '_setup_workers')
@patch.object(SetupWizard, '_setup_quality')
@patch.object(SetupWizard, '_setup_authentication')
def test_run_wizard_calls_all_setup_steps(mock_auth, mock_quality, mock_workers, mock_rate, mock_storage, mock_notify, mock_summary, mock_rich_io, mock_config_manager):
    """Test that all internal setup methods are called in sequence."""
    mock_rich_io["confirm"].return_value = True # Run setup
    
    SetupWizard.run(mock_config_manager)
    
    mock_auth.assert_called_once()
    mock_quality.assert_called_once()
    mock_workers.assert_called_once()
    mock_rate.assert_called_once()
    mock_storage.assert_called_once()
    mock_notify.assert_called_once()
    mock_summary.assert_called_once()

    # Assert final completion and save
    assert mock_config_manager.config.setup_completed is True
    mock_config_manager.save_config.assert_called() # Called multiple times during steps and at end


# --- Test _setup_authentication ---

def test_setup_auth_configures_cookies_file_if_valid(mock_rich_io, mock_config_manager, mock_path_exists):
    """Test configuration when user provides a valid file path."""
    mock_rich_io["confirm"].return_value = True  # Confirm setup
    mock_rich_io["prompt"].return_value = "/path/to/cookies.txt"
    
    SetupWizard._setup_authentication(mock_config_manager)
    
    assert mock_config_manager.config.cookies_file == "/path/to/cookies.txt"
    mock_config_manager.save_config.assert_called_once()


def test_setup_auth_skips_if_file_not_found(mock_rich_io, mock_config_manager):
    """Test configuration is skipped if file path is invalid."""
    mock_rich_io["confirm"].return_value = True
    mock_rich_io["prompt"].return_value = "/invalid/path.txt"
    
    with patch("pathlib.Path.exists", return_value=False):
        SetupWizard._setup_authentication(mock_config_manager)
    
    assert mock_config_manager.config.cookies_file is None


# --- Test _setup_quality ---

def test_setup_quality_sets_default_quality(mock_rich_io, mock_config_manager):
    """Test setting specific video and audio quality."""
    # Video: 2 (1080p), Audio: 3 (128kbps)
    mock_rich_io["prompt"].side_effect = ["2", "3"]
    
    SetupWizard._setup_quality(mock_config_manager)
    
    assert mock_config_manager.config.default_video_quality == "1080p"
    assert mock_config_manager.config.default_audio_quality == "128"
    mock_config_manager.save_config.assert_called_once()


# --- Test _setup_workers ---

def test_setup_workers_sets_valid_workers(mock_rich_io, mock_config_manager):
    """Test setting a valid number of workers (e.g., 5)."""
    mock_rich_io["intprompt"].return_value = 5
    
    SetupWizard._setup_workers(mock_config_manager)
    
    assert mock_config_manager.config.max_workers == 5
    mock_config_manager.save_config.assert_called_once()


def test_setup_workers_clamps_high_value(mock_rich_io, mock_config_manager):
    """Test that max_workers is clamped at the maximum limit (10)."""
    mock_rich_io["intprompt"].return_value = 15
    
    SetupWizard._setup_workers(mock_config_manager)
    
    assert mock_config_manager.config.max_workers == 10


# --- Test _setup_rate_limiting ---

def test_setup_rate_limiting_applies_moderate_preset(mock_rich_io, mock_config_manager):
    """Test setting the moderate preset (option 2)."""
    mock_rich_io["prompt"].return_value = "2"
    
    SetupWizard._setup_rate_limiting(mock_config_manager)
    
    assert mock_config_manager.config.max_downloads_per_hour == 50
    assert mock_config_manager.config.min_delay_seconds == 2.0
    assert mock_config_manager.config.max_delay_seconds == 5.0


def test_setup_rate_limiting_applies_custom_preset(mock_rich_io, mock_config_manager):
    """Test setting the custom preset (option 4)."""
    mock_rich_io["prompt"].side_effect = ["4", "120", "0.5", "1.5"]
    mock_rich_io["intprompt"].return_value = 120 # max_per_hour
    
    SetupWizard._setup_rate_limiting(mock_config_manager)
    
    assert mock_config_manager.config.max_downloads_per_hour == 120
    assert mock_config_manager.config.min_delay_seconds == 0.5
    assert mock_config_manager.config.max_delay_seconds == 1.5


# --- Test _setup_storage ---

# Mock StorageMenu dependency to avoid recursive imports
@patch('setup_wizard.StorageMenu', MagicMock())
def test_setup_storage_selects_local_and_skips(mock_rich_io, mock_config_manager):
    """Test selecting local storage (option 1) and skipping remote setup."""
    mock_rich_io["prompt"].return_value = "1"
    
    SetupWizard._setup_storage(mock_config_manager)
    
    # Assert StorageMenu.add_... methods were NOT called
    assert SetupWizard.StorageMenu.add_ftp_storage.call_count == 0


@patch('setup_wizard.StorageMenu', MagicMock())
def test_setup_storage_calls_ftp_method(mock_rich_io, mock_config_manager):
    """Test selecting remote (2) and then FTP (1)."""
    mock_rich_io["prompt"].side_effect = ["2", "1"]
    
    SetupWizard._setup_storage(mock_config_manager)
    
    # Assert the correct storage method was called
    SetupWizard.StorageMenu.add_ftp_storage.assert_called_once_with(mock_config_manager)
    # Assert other storage methods were NOT called
    assert SetupWizard.StorageMenu.add_sftp_storage.call_count == 0


# --- Test _setup_notifications ---

def test_setup_notifications_enables_slack(mock_rich_io, mock_config_manager):
    """Test configuring Slack notifications."""
    mock_rich_io["confirm"].return_value = True  # Confirm setup
    mock_rich_io["prompt"].return_value = "https://webhook.slack.com/test"
    
    SetupWizard._setup_notifications(mock_config_manager)
    
    assert mock_config_manager.config.slack_webhook_url == "https://webhook.slack.com/test"


def test_setup_notifications_skips_slack(mock_rich_io, mock_config_manager):
    """Test skipping Slack notifications."""
    mock_rich_io["confirm"].return_value = False # Decline setup
    mock_config_manager.config.slack_webhook_url = None
    
    SetupWizard._setup_notifications(mock_config_manager)
    
    assert mock_config_manager.config.slack_webhook_url is None
