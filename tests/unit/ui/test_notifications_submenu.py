"""Tests for notifications_submenu"""
import pytest
from unittest.mock import patch
from ui.notifications_submenu import NotificationsSubmenu


@pytest.fixture
def submenu(mock_config_manager):
    """Create NotificationsSubmenu instance"""
    with patch('ui.notifications_submenu.console'):
        return NotificationsSubmenu(mock_config_manager)


class TestNotificationsSubmenu:
    """Test suite for NotificationsSubmenu"""
    
    @patch('ui.notifications_submenu.Prompt.ask')
    def test_configure_slack(self, mock_prompt, submenu):
        """Test Slack configuration option"""
        mock_prompt.side_effect = ["1", "0"]
        submenu.show()
        submenu.config_manager.configure_slack_webhook.assert_called_once()
    
    @patch('ui.notifications_submenu.Prompt.ask')
    def test_configure_email(self, mock_prompt, submenu):
        """Test email configuration option"""
        mock_prompt.side_effect = ["2", "0"]
        submenu.show()
        submenu.config_manager.configure_email_notifications.assert_called_once()
    
    @patch('ui.notifications_submenu.Prompt.ask')
    def test_toggle_providers(self, mock_prompt, submenu):
        """Test toggle notification providers option"""
        mock_prompt.side_effect = ["3", "0"]
        submenu.show()
        submenu.config_manager.toggle_notification_provider.assert_called_once()
    
    @patch('ui.notifications_submenu.Prompt.ask')
    def test_configure_preferences(self, mock_prompt, submenu):
        """Test configure notification preferences option"""
        mock_prompt.side_effect = ["4", "0"]
        submenu.show()
        submenu.config_manager.configure_notification_preferences.assert_called_once()
    
    @patch('ui.notifications_submenu.Prompt.ask')
    def test_configure_alert_thresholds(self, mock_prompt, submenu):
        """Test configure alert thresholds option"""
        mock_prompt.side_effect = ["5", "0"]
        submenu.show()
        submenu.config_manager.configure_alert_thresholds.assert_called_once()
