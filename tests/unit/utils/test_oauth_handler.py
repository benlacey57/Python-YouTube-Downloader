import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from utils.oauth_handler import OAuthHandler


@pytest.fixture
def mock_datetime_now():
    """Patches datetime.now() for deterministic time control."""
    test_now = datetime(2025, 1, 1, 12, 0, 0)
    with patch('utils.oauth_handler.datetime') as mock_dt:
        mock_dt.now.return_value = test_now
        # Ensure we can still access timedelta
        mock_dt.timedelta = timedelta
        # Mock fromisoformat to be callable
        mock_dt.fromisoformat = datetime.fromisoformat
        yield mock_dt


# --- Test is_authenticated() ---

def test_is_authenticated_no_token():
    """Should return False if oauth_token is None."""
    handler = OAuthHandler(oauth_token=None)
    assert handler.is_authenticated() is False


def test_is_authenticated_token_valid(mock_datetime_now):
    """Should return True if token exists and expiry is in the future."""
    expiry_future = (mock_datetime_now.now() + timedelta(hours=1)).isoformat()
    handler = OAuthHandler(oauth_token="valid_token_xyz", oauth_expiry=expiry_future)
    assert handler.is_authenticated() is True


@patch.object(OAuthHandler, 'refresh_token', return_value=True)
def test_is_authenticated_token_expired_refresh_success(mock_refresh, mock_datetime_now):
    """Should attempt refresh if token is expired, and return result of refresh."""
    expiry_past = (mock_datetime_now.now() - timedelta(minutes=1)).isoformat()
    handler = OAuthHandler(oauth_token="expired_token", oauth_expiry=expiry_past)
    
    result = handler.is_authenticated()
    
    mock_refresh.assert_called_once()
    assert result is True


@patch.object(OAuthHandler, 'refresh_token', return_value=False)
def test_is_authenticated_token_expired_refresh_failure(mock_refresh, mock_datetime_now):
    """If refresh fails, authentication should fail."""
    expiry_past = (mock_datetime_now.now() - timedelta(minutes=1)).isoformat()
    handler = OAuthHandler(oauth_token="expired_token", oauth_expiry=expiry_past)
    
    result = handler.is_authenticated()
    
    mock_refresh.assert_called_once()
    assert result is False


def test_is_authenticated_invalid_expiry_format():
    """Should return False if oauth_expiry is not a valid ISO format string."""
    handler = OAuthHandler(oauth_token="token", oauth_expiry="not_a_date")
    assert handler.is_authenticated() is False


def test_is_authenticated_no_expiry_set():
    """If token exists but no expiry is set, assume it is valid (default safe mode)."""
    handler = OAuthHandler(oauth_token="perma_token", oauth_expiry=None)
    assert handler.is_authenticated() is True


# --- Test get_auth_header() ---

@patch.object(OAuthHandler, 'is_authenticated', return_value=True)
def test_get_auth_header_authenticated(mock_auth):
    """Should return the correct Authorization header if authenticated."""
    token = "final_token_123"
    handler = OAuthHandler(oauth_token=token)
    
    header = handler.get_auth_header()
    
    assert header == {"Authorization": f"Bearer {token}"}
    mock_auth.assert_called_once()


@patch.object(OAuthHandler, 'is_authenticated', return_value=False)
def test_get_auth_header_not_authenticated(mock_auth):
    """Should return None if not authenticated."""
    handler = OAuthHandler(oauth_token="token")
    
    header = handler.get_auth_header()
    
    assert header is None
    mock_auth.assert_called_once()


# --- Test Placeholder Methods ---

def test_authenticate_placeholder():
    """Placeholder method should return False."""
    handler = OAuthHandler()
    assert handler.authenticate() is False


def test_refresh_token_placeholder():
    """Placeholder method should return False."""
    handler = OAuthHandler()
    assert handler.refresh_token() is False
