"""Tests for advanced_settings_submenu"""
import pytest
from unittest.mock import patch, MagicMock
from ui.advanced_settings_submenu import AdvancedSettingsSubmenu


@pytest.fixture
def submenu(mock_config_manager):
    """Create AdvancedSettingsSubmenu instance"""
    with patch('ui.advanced_settings_submenu.console'):
        return AdvancedSettingsSubmenu(mock_config_manager)


class TestAdvancedSettingsSubmenu:
    """Test suite for AdvancedSettingsSubmenu"""
    
    @patch('ui.advanced_settings_submenu.Prompt.ask')
    def test_configure_live_streams(self, mock_prompt, submenu):
        """Test live streams configuration option"""
        mock_prompt.side_effect = ["1", "0"]
        submenu.show()
        submenu.config_manager.configure_live_streams.assert_called_once()
    
    @patch('ui.advanced_settings_submenu.Prompt.ask')
    @patch('ui.advanced_settings_submenu.input')
    @patch('ui.advanced_settings_submenu.StatusPage')
    def test_view_system_status(self, mock_status_class, mock_input, mock_prompt, submenu):
        """Test view system status option"""
        mock_prompt.side_effect = ["2", "0"]
        mock_status = MagicMock()
        mock_status_class.return_value = mock_status
        
        submenu.show()
        
        mock_status.show.assert_called_once()
        mock_input.assert_called_once()
    
    @patch('ui.advanced_settings_submenu.Prompt.ask')
    @patch('ui.advanced_settings_submenu.input')
    @patch('ui.advanced_settings_submenu.DatabaseSeeder')
    @patch('ui.advanced_settings_submenu.MonitorManager')
    @patch('ui.advanced_settings_submenu.Path')
    def test_seed_database(self, mock_path, mock_monitor_mgr, mock_seeder, mock_input, mock_prompt, submenu):
        """Test seed database option"""
        mock_prompt.side_effect = ["3", "0"]
        
        submenu.show()
        
        mock_seeder.assert_called_once()
        mock_input.assert_called_once()
    
    @patch('ui.advanced_settings_submenu.Prompt.ask')
    @patch('ui.advanced_settings_submenu.input')
    def test_migrate_configuration(self, mock_input, mock_prompt, submenu):
        """Test migrate configuration option"""
        mock_prompt.side_effect = ["4", "0"]
        submenu.show()
        submenu.config_manager.migrate_config.assert_called_once()
        mock_input.assert_called_once()
    
    @patch('ui.advanced_settings_submenu.Prompt.ask')
    @patch('ui.advanced_settings_submenu.input')
    def test_reset_configuration(self, mock_input, mock_prompt, submenu):
        """Test reset configuration option"""
        mock_prompt.side_effect = ["5", "0"]
        submenu.show()
        submenu.config_manager.reset_config.assert_called_once()
        mock_input.assert_called_once()
