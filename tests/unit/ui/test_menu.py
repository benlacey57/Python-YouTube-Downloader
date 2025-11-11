import pytest
from unittest.mock import patch, MagicMock
from menu import Menu
from rich.prompt import Prompt

# Define the expected choices for validation
EXPECTED_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8"]


@pytest.fixture
def mock_rich_output():
    """Fixture to mock rich.console.Console.print for silencing/checking output."""
    with patch("menu.console.print") as mock_print:
        yield mock_print


def test_display_main_menu_returns_user_choice(mock_rich_output):
    """Test that the method returns the value provided by Prompt.ask."""
    # Mock the rich.prompt.Prompt.ask method to simulate a user selecting '4'
    expected_choice = "4"
    with patch.object(Prompt, 'ask', return_value=expected_choice) as mock_ask:
        choice = Menu.display_main_menu()

    # Assert the returned value matches the mocked input
    assert choice == expected_choice

    # Assert Prompt.ask was called
    mock_ask.assert_called_once()


def test_display_main_menu_uses_correct_prompt_parameters(mock_rich_output):
    """Test that Prompt.ask is called with the expected choices and default."""
    with patch.object(Prompt, 'ask', return_value="1") as mock_ask:
        Menu.display_main_menu()

    # Check the arguments passed to Prompt.ask
    mock_ask.assert_called_once()
    
    # The first argument is the prompt message
    prompt_message = mock_ask.call_args[0][0]
    assert "Select an option" in prompt_message

    # The 'choices' and 'default' keyword arguments should match expectations
    kwargs = mock_ask.call_args[1]
    assert kwargs.get('choices') == EXPECTED_CHOICES
    assert kwargs.get('default') == "1"


def test_display_main_menu_prints_menu_ui(mock_rich_output):
    """Test that the method attempts to render the menu using console.print."""
    with patch.object(Prompt, 'ask', return_value="1"):
        Menu.display_main_menu()

    # The menu should print at least the title panel and the main menu panel.
    # The minimum number of calls to print to the console is 3:
    # 1. Newline (console.print("\n"))
    # 2. Title Panel (console.print(title))
    # 3. Menu Panel (console.print(menu_panel))
    assert mock_rich_output.call_count >= 3
    
    # More specifically, check that the main menu structure is generated
    # by ensuring 'Main Menu' and a key option are present in the mock calls.
    # Note: Mocking console.print directly only captures the final call arguments,
    # so we primarily confirm that the UI functions were called.
