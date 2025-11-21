# Test Suite

Comprehensive test suite for YouTube Playlist Downloader.

## Quick Start

```bash
# Run all tests
make test

# Or use pytest directly
python3 -m pytest tests/ -v

# Run with coverage report
python3 -m pytest tests/ --cov=. --cov-report=term-missing

# Run interactive test menu
python3 tests/run.py
```

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── run.py                   # Interactive test runner
├── TEST_STATUS.md           # Test coverage status and todo list
├── README.md                # This file
└── unit/                    # Unit tests
    ├── downloaders/         # Downloader tests
    ├── managers/            # Manager tests
    ├── models/              # Model/dataclass tests
    ├── notifiers/           # Notification tests
    ├── ui/                  # UI component tests
    └── utils/               # Utility function tests
```

## Shared Fixtures

All fixtures are centralized in `conftest.py`:

### Configuration
- `mock_config` - Mock config object with defaults
- `mock_config_manager` - Mock ConfigManager

### Models
- `sample_queue` - Sample Queue object
- `sample_download_item` - Sample DownloadItem
- `sample_channel` - Sample Channel
- `sample_daily_stats` - Sample DailyStats

### Managers
- `mock_stats_manager` - Mock StatsManager
- `mock_queue_manager` - Mock QueueManager
- `mock_notification_manager` - Mock NotificationManager
- `mock_proxy_manager` - Mock ProxyManager

### Other
- `temp_test_dir` - Temporary directory for file tests
- `mock_file_operations` - Mock file system operations
- `mock_yt_dlp` - Mock yt-dlp library
- `mock_requests` - Mock requests library
- `mock_datetime` - Mock datetime for consistent time

## Writing Tests

### Basic Test Example

```python
import pytest
from unittest.mock import patch

def test_my_function(mock_config_manager):
    """Test description"""
    # Arrange
    expected = "result"
    
    # Act
    result = my_function(mock_config_manager)
    
    # Assert
    assert result == expected
```

### Using Fixtures

```python
def test_with_queue(sample_queue, mock_queue_manager):
    """Test using sample queue"""
    mock_queue_manager.get_queue.return_value = sample_queue
    # ... test code
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test", "TEST"),
    ("hello", "HELLO"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### Marking Tests

```python
@pytest.mark.live
def test_network_request():
    """This test requires network access"""
    # ... test code

@pytest.mark.managers
def test_config_manager():
    """This is a manager test"""
    # ... test code
```

## Test Markers

Configure in `pytest.ini`:
- `live` - Tests requiring external network (skipped by default)
- `managers` - Manager/business logic tests
- `models` - Data model tests
- `ui` - User interface tests
- `utils` - Utility function tests

### Running Specific Tests

```bash
# Run only manager tests
pytest -m managers

# Exclude live tests (default)
pytest -m "not live"

# Run specific test file
pytest tests/unit/ui/test_menu.py -v

# Run specific test function
pytest tests/unit/ui/test_menu.py::test_show_menu -v
```

## Coverage

Target: **80% code coverage**

Check current coverage:
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

Focus areas:
1. Critical download path
2. Database operations
3. Error handling
4. User input validation

## Best Practices

1. **Isolate Tests** - Each test should be independent
2. **Mock External Deps** - No real network calls or file I/O
3. **Clear Names** - `test_<function>_<scenario>_<result>`
4. **Arrange-Act-Assert** - Structure tests clearly
5. **Use Fixtures** - Reuse setup code via conftest.py
6. **Parametrize** - Test multiple inputs efficiently
7. **Test Edge Cases** - Not just happy path

## Common Patterns

### Mocking Console Output

```python
@patch('ui.menu.console')
def test_print_menu(mock_console):
    show_menu()
    mock_console.print.assert_called()
```

### Testing User Input

```python
@patch('ui.menu.Prompt.ask')
def test_user_choice(mock_prompt):
    mock_prompt.return_value = "1"
    choice = get_user_choice()
    assert choice == "1"
```

### Testing File Operations

```python
def test_save_file(temp_test_dir):
    """Use temp_test_dir fixture"""
    file_path = temp_test_dir / "test.txt"
    save_file(file_path, "content")
    assert file_path.exists()
```

## Continuous Integration

Tests can be integrated with CI/CD:

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Import Errors
- Make sure you're running from project root
- Check sys.path includes project root (conftest.py handles this)

### Fixture Not Found
- Check fixture is in conftest.py
- Check spelling matches exactly

### Tests Hanging
- Mock all external I/O (network, file system)
- Check for infinite loops in test code

### Coverage Too Low
- Run with `--cov-report=html` to see missed lines
- Add tests for error paths and edge cases

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Test Status](TEST_STATUS.md) - Current test coverage
