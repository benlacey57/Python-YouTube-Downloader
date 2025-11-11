import pytest
from unittest.mock import patch, MagicMock, NonCallableMock, call
from abc import ABC, abstractmethod
from pathlib import Path

# Assuming StorageProvider and derived classes are accessible
from utils.storage_providers import (
    StorageProvider, StorageManager,
    FTPStorage, SFTPStorage, GoogleDriveStorage, DropboxStorage, OneDriveStorage
)

# Mock the rich console for all tests
class MockConsole:
    def print(self, *args, **kwargs):
        pass

@pytest.fixture(scope="module", autouse=True)
def mock_rich_console():
    """Patches the rich console globally to prevent test output."""
    with patch('utils.storage_providers.console', MockConsole()):
        yield

# --- Test StorageProvider Base Class ---

def test_storage_provider_is_abstract():
    """Verify that StorageProvider cannot be instantiated directly."""
    with pytest.raises(TypeError) as excinfo:
        StorageProvider()
    assert "Can't instantiate abstract class StorageProvider" in str(excinfo.value)


# --- Test StorageManager ---

@pytest.fixture
def mock_concrete_provider():
    """Mock a concrete implementation of StorageProvider."""
    provider = MagicMock(spec=StorageProvider)
    provider.is_connected.return_value = False
    provider.connect.return_value = True
    provider.upload_file.return_value = True
    return provider

@pytest.fixture
def storage_manager_instance(mock_concrete_provider):
    """Provides an initialized StorageManager."""
    manager = StorageManager()
    manager.add_provider("test_ftp", mock_concrete_provider)
    manager.add_provider("test_sftp", mock_concrete_provider)
    manager.set_active_provider("test_ftp")
    return manager


def test_storage_manager_add_and_get_active(storage_manager_instance, mock_concrete_provider):
    """Test adding a provider and setting it as active."""
    assert storage_manager_instance.get_active_provider() == mock_concrete_provider


def test_storage_manager_set_active_provider_missing(storage_manager_instance):
    """Test setting an active provider that hasn't been added."""
    assert storage_manager_instance.set_active_provider("missing") is False
    assert storage_manager_instance.active_provider == "test_ftp" # Unchanged


def test_storage_manager_get_active_provider_none():
    """Test getting active provider when none is set."""
    manager = StorageManager()
    assert manager.get_active_provider() is None


def test_storage_manager_upload_success(storage_manager_instance, mock_concrete_provider):
    """Test successful upload, including connecting first."""
    result = storage_manager_instance.upload_file("local.txt", "remote/path.txt")
    
    mock_concrete_provider.is_connected.assert_called_once()
    mock_concrete_provider.connect.assert_called_once()
    mock_concrete_provider.upload_file.assert_called_once_with("local.txt", "remote/path.txt")
    assert result is True


def test_storage_manager_upload_already_connected(storage_manager_instance, mock_concrete_provider):
    """Test successful upload when already connected."""
    mock_concrete_provider.is_connected.return_value = True
    mock_concrete_provider.upload_file.return_value = True
    
    result = storage_manager_instance.upload_file("local.txt", "remote/path.txt")
    
    mock_concrete_provider.connect.assert_not_called()
    assert result is True


def test_storage_manager_upload_connect_failure(storage_manager_instance, mock_concrete_provider):
    """Test failure when provider fails to connect."""
    mock_concrete_provider.connect.return_value = False
    
    result = storage_manager_instance.upload_file("local.txt", "remote/path.txt")
    
    mock_concrete_provider.connect.assert_called_once()
    mock_concrete_provider.upload_file.assert_not_called()
    assert result is False


def test_storage_manager_upload_no_active_provider():
    """Test upload fails if no provider is active."""
    manager = StorageManager()
    assert manager.upload_file("local.txt", "remote.txt") is False


# --- Test Individual Provider Connection Logic (using Mocks for external libs) ---

# FTP Storage Mocks
@patch('utils.storage_providers.FTP')
def test_ftp_storage_connect_success_anonymous(mock_ftp_class):
    """Test successful anonymous FTP connection."""
    mock_ftp_instance = mock_ftp_class.return_value
    storage = FTPStorage(host="ftp.anon.com")
    
    assert storage.connect() is True
    mock_ftp_instance.connect.assert_called_once_with("ftp.anon.com", 21, timeout=30)
    mock_ftp_instance.login.assert_called_once_with()
    mock_ftp_instance.cwd.assert_not_called()


@patch('utils.storage_providers.FTP')
def test_ftp_storage_connect_success_authenticated_with_path(mock_ftp_class):
    """Test successful authenticated FTP connection and CWD."""
    mock_ftp_instance = mock_ftp_class.return_value
    storage = FTPStorage(host="ftp.auth.com", username="u", password="p", base_path="/remote/data")
    
    assert storage.connect() is True
    mock_ftp_instance.login.assert_called_once_with("u", "p")
    mock_ftp_instance.cwd.assert_called_once_with("/remote/data")


@patch('utils.storage_providers.FTP', side_effect=Exception("FTP error"))
def test_ftp_storage_connect_failure(mock_ftp_class):
    """Test failed FTP connection."""
    storage = FTPStorage(host="ftp.fail.com")
    assert storage.connect() is False
    assert storage.ftp is None


@patch('utils.storage_providers.FTP')
def test_ftp_storage_disconnect(mock_ftp_class):
    """Test FTP disconnection."""
    mock_ftp_instance = mock_ftp_class.return_value
    storage = FTPStorage(host="h")
    storage.ftp = mock_ftp_instance # Simulate being connected
    
    storage.disconnect()
    mock_ftp_instance.quit.assert_called_once()


@patch('utils.storage_providers.FTP')
def test_ftp_storage_is_connected(mock_ftp_class):
    """Test FTP connection check (NOOP command)."""
    mock_ftp_instance = mock_ftp_class.return_value
    storage = FTPStorage(host="h")
    storage.ftp = mock_ftp_instance
    
    # Connected
    mock_ftp_instance.voidcmd.return_value = '200 OK'
    assert storage.is_connected() is True
    
    # Disconnected
    mock_ftp_instance.voidcmd.side_effect = Exception
    assert storage.is_connected() is False


# SFTP Storage Mocks
@patch('utils.storage_providers.Path.exists', return_value=False) # No key file
@patch('utils.storage_providers.paramiko')
def test_sftp_storage_connect_password_success(mock_paramiko, mock_path_exists):
    """Test successful SFTP connection using password."""
    mock_transport = mock_paramiko.Transport.return_value
    storage = SFTPStorage(host="sftp.com", username="u", password="p", port=22)
    
    assert storage.connect() is True
    mock_transport.connect.assert_called_once_with(username="u", password="p")
    mock_paramiko.SFTPClient.from_transport.assert_called_once_with(mock_transport)
    assert storage.sftp is not None


@patch('utils.storage_providers.Path.exists', return_value=True) # Key file exists
@patch('utils.storage_providers.paramiko')
def test_sftp_storage_connect_key_success(mock_paramiko, mock_path_exists):
    """Test successful SFTP connection using key file."""
    mock_transport = mock_paramiko.Transport.return_value
    mock_rsa_key = mock_paramiko.RSAKey.from_private_key_file.return_value
    
    storage = SFTPStorage(host="sftp.com", username="u", key_filename="/id_rsa")
    
    assert storage.connect() is True
    mock_paramiko.RSAKey.from_private_key_file.assert_called_once_with("/id_rsa")
    mock_transport.connect.assert_called_once_with(username="u", pkey=mock_rsa_key)
    assert storage.sftp is not None
