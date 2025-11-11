import pytest
import time
import smtplib
from unittest.mock import MagicMock, patch, call
from email.mime.text import MIMEText

# Mock smtplib and time modules before importing SMTPNotifier
mock_smtplib = MagicMock()
mock_time = MagicMock()

with patch.dict('sys.modules', {'smtplib': mock_smtplib, 'time': mock_time}):
    from notifiers.smtp_notifier import SMTPNotifier

# --- Fixtures ---

@pytest.fixture
def mock_smtp_server():
    """Mock the smtplib.SMTP class and instance."""
    mock_server_instance = MagicMock(spec=smtplib.SMTP)
    mock_smtplib.SMTP.return_value = mock_server_instance
    return mock_server_instance

@pytest.fixture
def valid_smtp_config():
    """Valid configuration dictionary for SMTPNotifier."""
    return {
        'host': 'smtp.mock.com',
        'port': 587,
        'user': 'test_user',
        'password': 'test_password',
        'sender_email': 'sender@mock.com',
        'recipient_email': 'recipient@mock.com',
        'use_tls': True
    }

@pytest.fixture
def configured_notifier(valid_smtp_config):
    """SMTPNotifier configured with valid credentials."""
    return SMTPNotifier(smtp_config=valid_smtp_config)

@pytest.fixture
def unconfigured_notifier():
    """SMTPNotifier with missing essential credentials."""
    return SMTPNotifier(smtp_config={'host': 'h', 'port': 25})

# --- General Tests ---

def test_is_configured(configured_notifier, unconfigured_notifier):
    """Test is_configured returns correctly based on config completeness."""
    assert configured_notifier.is_configured() is True
    assert unconfigured_notifier.is_configured() is False

# --- send_notification Tests ---

def test_send_notification_unconfigured(unconfigured_notifier):
    """Unconfigured notifier should return False and not attempt connection."""
    assert unconfigured_notifier.send_notification("T", "M") is False
    mock_smtplib.SMTP.assert_not_called()

@patch('email.mime.text.MIMEText')
def test_send_notification_success(mock_mime_text_class, mock_smtp_server, configured_notifier, valid_smtp_config):
    """Test successful email sending process."""
    mock_message_object = MagicMock()
    mock_mime_text_class.return_value = mock_message_object
    
    result = configured_notifier.send_notification("Alert Title", "Email Body")
    
    assert result is True
    
    # 1. Verify SMTP connection
    mock_smtplib.SMTP.assert_called_once_with(valid_smtp_config['host'], valid_smtp_config['port'], timeout=10)
    
    # 2. Verify TLS and login
    mock_smtp_server.starttls.assert_called_once()
    mock_smtp_server.login.assert_called_once_with(valid_smtp_config['user'], valid_smtp_config['password'])
    
    # 3. Verify sendmail
    mock_smtp_server.sendmail.assert_called_once_with(
        valid_smtp_config['sender_email'],
        valid_smtp_config['recipient_email'],
        mock_message_object.as_string()
    )
    
    # 4. Verify MIMEText creation (Subject/From/To set on the object)
    mock_mime_text_class.assert_called_once_with("Email Body", 'plain')
    assert mock_message_object.__setitem__.call_args_list == [
        call('Subject', '[PD] Alert Title'),
        call('From', 'sender@mock.com'),
        call('To', 'recipient@mock.com')
    ]
    
    # 5. Verify server quit
    mock_smtp_server.quit.assert_called_once()

def test_send_notification_exception(mock_smtp_server, configured_notifier):
    """Test handling of SMTP exception during connection or sending."""
    mock_smtp_server.starttls.side_effect = smtplib.SMTPException("Auth failed")
    
    with patch('notifiers.smtp_notifier.console') as mock_console:
        result = configured_notifier.send_notification("T", "M")
        
    assert result is False
    mock_console.print.assert_called()

# --- Specific Notifier Methods Tests (check title/message formatting) ---

def test_notify_queue_completed_success(configured_notifier):
    """Test notify_queue_completed (success) calls send_notification correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    mock_time.strftime.return_value = "2025-11-11 10:00:00"
    
    configured_notifier.notify_queue_completed("List X", 10, 0, 10, "5h")
    
    title_arg, message_arg, _ = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == "Queue Completed successfully: List X"
    assert "Status: Completed successfully" in message_arg
    assert "Downloaded: 10/10" in message_arg
    assert "Time: 2025-11-11 10:00:00" in message_arg

def test_notify_queue_completed_with_errors(configured_notifier):
    """Test notify_queue_completed (with errors) calls send_notification correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    
    configured_notifier.notify_queue_completed("List Y", 8, 2, 10, "1h")
    
    title_arg, message_arg, _ = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == "Queue Completed with errors: List Y"
    assert "Status: Completed with errors" in message_arg
    assert "Failed: 2" in message_arg

def test_notify_queue_failed(configured_notifier):
    """Test notify_queue_failed calls send_notification correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    
    configured_notifier.notify_queue_failed("List Z", "Connection Reset")
    
    title_arg, message_arg, _ = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == "Queue Failed: List Z"
    assert "Error: Connection Reset" in message_arg

def test_notify_size_threshold(configured_notifier):
    """Test notify_size_threshold calls send_notification correctly."""
    configured_notifier.send_notification = MagicMock(return_value=True)
    
    configured_notifier.notify_size_threshold(5000, 5001.234)
    
    title_arg, message_arg, _ = configured_notifier.send_notification.call_args[0]
    
    assert title_arg == "Download Size Alert: 5000 MB Reached"
    assert "Threshold: 5000 MB" in message_arg
    assert "Total Downloaded Today: 5001.23 MB" in message_arg
