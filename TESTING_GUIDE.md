# Testing Guide

## Overview

This project uses pytest for testing with comprehensive unit and integration test coverage.

## Running Tests

### Run All Tests

```bash
make test
```

### Run Tests with Coverage Report

```bash
make test-coverage
```

This generates both terminal output and an HTML report in `htmlcov/index.html`.

### Run Specific Test File

```bash
make test-file FILE=tests/unit/managers/test_queue_manager.py
```

### Run Tests by Pattern

```bash
# Run all manager tests
pytest tests/unit/managers/ -v

# Run all tests matching a pattern
pytest -k "queue" -v

# Run tests in a specific module
pytest tests/unit/downloaders/test_video_downloader.py::TestVideoDownloader::test_download_quality -v
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (isolated component tests)
│   ├── managers/           # Manager tests
│   ├── downloaders/        # Downloader tests
│   ├── models/             # Model tests
│   ├── notifiers/          # Notifier tests
│   ├── utils/              # Utility tests
│   └── ui/                 # UI component tests
└── integration/            # Integration tests (component interactions)
    ├── test_download_workflow.py
    ├── test_queue_workflow.py
    └── test_notification_workflow.py
```

## Writing Tests

### Test File Naming

- Unit tests: `test_<module_name>.py`
- Test class: `Test<ClassName>`
- Test method: `test_<function_name>_<scenario>`

Example:
```python
# tests/unit/managers/test_queue_manager.py
class TestQueueManager:
    def test_create_queue_success(self):
        pass
    
    def test_create_queue_invalid_data(self):
        pass
```

### Using Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
def test_something(mock_config, temp_database):
    # mock_config provides a test configuration
    # temp_database provides a temporary test database
    manager = QueueManager()
    # ... test code
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_download_with_ydl(mocker):
    # Mock yt-dlp to avoid real network calls
    mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
    mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {
        'title': 'Test Video',
        'id': '12345'
    }
    
    # Test your code
    result = download_video('http://example.com')
    assert result.title == 'Test Video'
```

### Testing Async/Threaded Code

```python
import time
from threading import Thread

def test_keyboard_handler_pause():
    from utils.keyboard_handler import keyboard_handler
    
    # Start in a thread
    keyboard_handler.start_listening()
    
    # Test pause
    keyboard_handler.pause()
    assert keyboard_handler.is_paused() == True
    
    # Cleanup
    keyboard_handler.stop_listening()
```

## Test Coverage Goals

### Current Coverage: ~34%
### Target Coverage: 75%+

Priority areas:
1. **Managers** (queue, stats, notification) - 100% target
2. **Downloaders** (base, video, audio) - 90% target
3. **Utils** (rate_limiter, keyboard_handler) - 80% target
4. **UI Components** - 70% target

## Best Practices

### 1. Isolate Tests

Each test should be independent and not rely on other tests.

```python
# Good
def test_create_queue(temp_database):
    manager = QueueManager()
    queue = manager.create_queue(sample_queue())
    assert queue.id is not None

# Bad - depends on previous test
def test_get_queue():
    queue = manager.get_queue(1)  # Assumes queue 1 exists
```

### 2. Use Descriptive Names

```python
# Good
def test_download_item_with_proxy_rotation():
    pass

# Bad
def test_download():
    pass
```

### 3. Test Edge Cases

```python
def test_create_queue_with_empty_title():
    """Test that queue creation fails with empty title"""
    pass

def test_download_with_network_timeout():
    """Test download handles network timeout gracefully"""
    pass

def test_rate_limiter_at_max_downloads():
    """Test rate limiter blocks when max downloads reached"""
    pass
```

### 4. Mock External Services

Never make real API calls or network requests in tests:

```python
# Mock yt-dlp
@patch('yt_dlp.YoutubeDL')
def test_download(mock_ydl):
    pass

# Mock file operations
@patch('pathlib.Path.exists')
def test_file_check(mock_exists):
    pass

# Mock time
@patch('time.sleep')
def test_rate_limit(mock_sleep):
    pass
```

### 5. Clean Up Resources

Use fixtures with cleanup or context managers:

```python
@pytest.fixture
def temp_download_dir():
    """Create temporary directory for downloads"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)
```

## Common Testing Patterns

### Testing Database Operations

```python
def test_create_and_retrieve_queue(temp_database):
    manager = QueueManager()
    
    # Create
    queue = Queue(
        playlist_url="http://example.com",
        playlist_title="Test Playlist"
    )
    queue_id = manager.create_queue(queue)
    
    # Retrieve
    retrieved = manager.get_queue(queue_id)
    assert retrieved.playlist_title == "Test Playlist"
```

### Testing Error Handling

```python
def test_download_handles_network_error(mocker):
    mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
    mock_ydl.side_effect = Exception("Network error")
    
    downloader = VideoDownloader()
    result = downloader.download_item(sample_item(), sample_queue())
    
    assert result.status == "failed"
    assert "Network error" in result.error
```

### Testing UI Components

```python
def test_menu_navigation(mocker):
    # Mock user input
    mock_prompt = mocker.patch('rich.prompt.Prompt.ask')
    mock_prompt.side_effect = ["1", "0"]  # Select option 1, then exit
    
    menu = Menu()
    # Test that menu doesn't crash
    # and calls expected methods
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch commits
- Release tags

### CI Configuration

GitHub Actions workflow (`.github/workflows/test.yml`):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: make install
      - name: Run tests
        run: make test-coverage
```

## Debugging Failed Tests

### Run with verbose output

```bash
pytest tests/unit/managers/test_queue_manager.py -vv
```

### Run with print statements visible

```bash
pytest tests/ -s
```

### Run specific test with debugger

```bash
pytest tests/unit/managers/test_queue_manager.py::TestQueueManager::test_create_queue --pdb
```

### Show local variables on failure

```bash
pytest tests/ -l
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Getting Help

- Check `TEST_COVERAGE_ANALYSIS.md` for current coverage status
- Review existing tests in `tests/` for patterns
- See `tests/conftest.py` for available fixtures
