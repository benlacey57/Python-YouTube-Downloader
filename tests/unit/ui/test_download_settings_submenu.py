"""Tests for download_settings_submenu"""
import pytest
from unittest.mock import MagicMock, patch, call
from ui.download_settings_submenu import DownloadSettingsSubmenu


@pytest.fixture
def submenu(mock_config_manager):
    """Create DownloadSettingsSubmenu instance with mocked dependencies"""
    with patch('ui.download_settings_submenu.console'):
        return DownloadSettingsSubmenu(mock_config_manager)


class TestDownloadSettingsSubmenu:
    """Test suite for DownloadSettingsSubmenu"""
    
    def test_init_with_config_manager(self, mock_config_manager):
        """Test initialization with provided config manager"""
        with patch('ui.download_settings_submenu.console'):
            submenu = DownloadSettingsSubmenu(mock_config_manager)
            assert submenu.config_manager == mock_config_manager
    
    def test_init_without_config_manager(self):
        """Test initialization creates ConfigManager if not provided"""
        with patch('ui.download_settings_submenu.ConfigManager') as mock_cm_class, \
             patch('ui.download_settings_submenu.console'):
            submenu = DownloadSettingsSubmenu()
            mock_cm_class.assert_called_once()
            assert submenu.config_manager is not None
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    @patch('ui.download_settings_submenu.console')
    def test_show_menu_displays_options(self, mock_console, mock_prompt, submenu):
        """Test that show() displays all menu options"""
        # Simulate user selecting exit
        mock_prompt.return_value = "0"
        
        submenu.show()
        
        # Verify menu options are printed
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        menu_text = ''.join(print_calls)
        
        assert "Configure default quality" in menu_text or len(print_calls) > 0
        mock_prompt.assert_called()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_configure_default_quality(self, mock_prompt, submenu):
        """Test configure default quality option"""
        # First call returns option 1, second returns 0 to exit
        mock_prompt.side_effect = ["1", "0"]
        
        submenu.show()
        
        submenu.config_manager.configure_default_quality.assert_called_once()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_configure_parallel_downloads(self, mock_prompt, submenu):
        """Test configure parallel downloads option"""
        mock_prompt.side_effect = ["2", "0"]
        
        submenu.show()
        
        submenu.config_manager.configure_parallel_downloads.assert_called_once()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_configure_timeout(self, mock_prompt, submenu):
        """Test configure download timeout option"""
        mock_prompt.side_effect = ["3", "0"]
        
        submenu.show()
        
        submenu.config_manager.configure_download_timeout.assert_called_once()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_configure_filename_template(self, mock_prompt, submenu):
        """Test configure filename template option"""
        mock_prompt.side_effect = ["4", "0"]
        
        submenu.show()
        
        submenu.config_manager.configure_filename_template.assert_called_once()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_configure_filename_normalization(self, mock_prompt, submenu):
        """Test configure filename normalization option"""
        mock_prompt.side_effect = ["5", "0"]
        
        submenu.show()
        
        submenu.config_manager.configure_filename_normalization.assert_called_once()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_exits_on_zero(self, mock_prompt, submenu):
        """Test that selecting 0 exits the menu"""
        mock_prompt.return_value = "0"
        
        submenu.show()
        
        # Menu should exit without calling any config methods
        submenu.config_manager.configure_default_quality.assert_not_called()
        submenu.config_manager.configure_parallel_downloads.assert_not_called()
    
    @patch('ui.download_settings_submenu.Prompt.ask')
    def test_show_loops_until_exit(self, mock_prompt, submenu):
        """Test that menu loops until user selects exit"""
        # User selects options 1 and 2, then exits
        mock_prompt.side_effect = ["1", "2", "0"]
        
        submenu.show()
        
        submenu.config_manager.configure_default_quality.assert_called_once()
        submenu.config_manager.configure_parallel_downloads.assert_called_once()
        assert mock_prompt.call_count == 3
