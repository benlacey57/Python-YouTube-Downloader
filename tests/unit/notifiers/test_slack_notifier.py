import pytest
import time
from unittest.mock import MagicMock, patch, call

# Mock the requests and time modules before importing SlackNotifier
mock_requests = MagicMock()
mock_time = MagicMock()

with patch.dict('sys.modules', {'requests': mock_requests, 'time': mock_time}):
    from notifiers.slack_notifier import SlackNotifier

# --- Fixtures ---

@pytest.fixture
def mock_slack_response():
    """Mock a successful HTTP response from Slack."""
    response = MagicMock()
    response.status_code = 200
    return response

@pytest.fixture
def configured_notifier(mock_slack_response):
    """Notifier configured with a mock URL."""
    notifier = SlackNotifier(webhook_url="http://mock.slack.webhook/123")
    mock_requests.post.return_value = mock_slack_response
    return notifier

@pytest.fixture
def unconfigured_notifier():
    """Notifier with no webhook URL."""
    return SlackNotifier(webhook_url=None)

# --- General Tests ---

def test_is_configured(configured_notifier, unconfigured_notifier):
    """Test is_configured returns correctly based on webhook_url."""
    assert configured_notifier.is_configured() is True
    assert unconfigured_notifier.is_configured() is False

# --- send_notification Tests ---

def test_send_notification_unconfigured(unconfigured_notifier):
    """Unconfigured notifier should return False and not call requests.post."""
    assert unconfigured_notifier.send_notification("T", "M") is False
    mock_requests.post.assert_not_called()

def test_send_notification_success(configured_notifier, mock_slack_response):
    """Test successful API call."""
    mock_time.time.return_value = 1678886400  # Mock timestamp
    
    result = configured_notifier.send_notification("My Title", "My Message", color="danger")
    
    assert result is True
    
    # Verify requests.post was called with the correct payload structure
    mock_requests.post.assert_called_once()
    
    # Extract the payload argument
    _, kwargs = mock_requests.post.call_args
    payload = kwargs['json']
    
    assert payload['attachments'][0]['color'] == 'danger'
    assert payload['attachments'][0]['title'] == 'My Title'
    assert payload['attachments'][0]['text'] == 'My Message'
    assert payload['attachments'][0]['ts'] == 1678886400


def test_send_notification_failure_status_code(configured_notifier):
    """Test failure due to non-200 status code."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_requests.post.return_value = mock_response
    
    assert configured_notifier.send_notification("T", "M") is False

def test_send_notification_exception(configured_notifier):
    """Test failure due to network exception."""
    mock_requests.post.side_effect = Exception("Network Down")
    
    with patch('notifiers.slack_notifier.console') as mock_console:
        result = configured_notifier.send_notification("T", "M")
        
    assert result is False
    mock_console.print.assert_called()

# --- Specific Notifier Methods Tests ---

@pytest.mark.parametrize("failed, color, status_title", [
    (0, "good", "Queue Completed successfully"),
    (1, "warning", "Queue Completed with errors"),
])
def test_notify_queue_completed(configured_notifier, failed, color, status_title):
    """Test notify_queue_completed formats message correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    
    result = configured_notifier.notify_queue_completed("List A", 5, failed, 6, "1h 30m")
    
    assert result is True
    configured_notifier.send_notification.assert_called_once()
    
    title_arg, message_arg, color_arg = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == status_title
    assert color_arg == color
    assert "*Playlist:* List A" in message_arg
    assert "*Downloaded:* 5/6" in message_arg
    assert "*Duration:* 1h 30m" in message_arg


def test_notify_monitoring_update(configured_notifier):
    """Test notify_monitoring_update formats message correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    
    configured_notifier.notify_monitoring_update("Channel B", 12)
    
    title_arg, message_arg, color_arg = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == "New Videos Detected"
    assert color_arg == "#36a64f"
    assert "*Playlist:* Channel B" in message_arg
    assert "*New Videos:* 12" in message_arg

def test_notify_size_threshold(configured_notifier):
    """Test notify_size_threshold formats message correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    mock_time.strftime.return_value = "11:30:00"
    
    configured_notifier.notify_size_threshold(1024, 1500.75)
    
    title_arg, message_arg, color_arg = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == "Download Size Alert: 1024 MB Reached"
    assert color_arg == "warning"
    assert "*Threshold:* 1024 MB" in message_arg
    assert "*Total Downloaded Today:* 1500.75 MB" in message_arg
    assert "*Time:* 11:30:00" in message_arg
