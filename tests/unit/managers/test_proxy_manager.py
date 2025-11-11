import pytest
import csv
import random
import requests
from unittest.mock import MagicMock, patch, mock_open, call
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Import the class to be tested (assuming proxy_manager.py is accessible)
from proxy_manager import ProxyManager

# --- Mock Dependencies ---

# Mock the rich console for all tests
class MockConsole:
    def print(self, *args, **kwargs):
        pass

@pytest.fixture(scope="module", autouse=True)
def mock_rich_console():
    """Patches the rich console globally to prevent test output."""
    with patch('proxy_manager.console', MockConsole()):
        yield

# Mock the external file paths
@pytest.fixture
def mock_path_exists():
    """Patches Path.exists to control which file is 'found'."""
    with patch('proxy_manager.Path.exists') as mock_exists:
        # Default to False unless explicitly set in a test
        mock_exists.return_value = False
        yield mock_exists

# Mock the Confirmation Prompt for interactive methods
@pytest.fixture
def mock_confirm():
    """Patches rich.prompt.Confirm.ask to provide a default answer."""
    with patch('proxy_manager.Confirm.ask') as mock_confirm:
        yield mock_confirm

# --- Fixtures ---

@pytest.fixture
def proxy_manager_instance():
    """Provides a fresh ProxyManager instance."""
    return ProxyManager()

@pytest.fixture
def initialized_manager():
    """Provides a ProxyManager initialized with a list of proxies."""
    return ProxyManager(proxies=["http://1.1.1.1:80", "http://2.2.2.2:8080", "https://3.3.3.3:443"])

# --- Tests for Initialization and Rotation ---

def test_init_with_no_proxies():
    manager = ProxyManager()
    assert manager.proxies == []
    assert manager.current_index == 0

def test_init_with_proxies():
    proxies = ["p1", "p2"]
    manager = ProxyManager(proxies=proxies)
    assert manager.proxies == proxies
    assert manager.current_index == 0

# --- Rotation Tests ---

def test_get_next_proxy_rotation(initialized_manager):
    assert initialized_manager.get_next_proxy() == "http://1.1.1.1:80"
    assert initialized_manager.get_next_proxy() == "http://2.2.2.2:8080"
    assert initialized_manager.get_next_proxy() == "https://3.3.3.3:443"
    # Wrap around
    assert initialized_manager.get_next_proxy() == "http://1.1.1.1:80"
    assert initialized_manager.current_index == 1

def test_get_next_proxy_empty(proxy_manager_instance):
    assert proxy_manager_instance.get_next_proxy() is None

@patch('random.choice')
def test_get_random_proxy(mock_random_choice, initialized_manager):
    mock_random_choice.return_value = "https://3.3.3.3:443"
    assert initialized_manager.get_random_proxy() == "https://3.3.3.3:443"
    mock_random_choice.assert_called_once_with(initialized_manager.proxies)

def test_get_random_proxy_empty(proxy_manager_instance):
    assert proxy_manager_instance.get_random_proxy() is None

# --- Tests for Loading Proxies from File (.txt) ---

def test_load_proxies_from_txt_success(proxy_manager_instance, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.txt") # Only proxies.txt exists
    
    mock_file_content = "http://1.1.1.1:80\n# comment\n  \nhttps://2.2.2.2:443\n"
    
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        result = proxy_manager_instance.load_proxies_from_file()

    assert result is True
    assert proxy_manager_instance.proxies == ["http://1.1.1.1:80", "https://2.2.2.2:443"]

def test_load_proxies_from_txt_file_not_found(proxy_manager_instance, mock_path_exists):
    # Both files default to not existing
    result = proxy_manager_instance.load_proxies_from_file()
    assert result is False
    assert proxy_manager_instance.proxies == []

@patch("builtins.open", side_effect=IOError("Permission denied"))
def test_load_proxies_from_txt_io_error(mock_open_func, proxy_manager_instance, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.txt")
    
    result = proxy_manager_instance.load_proxies_from_file()
    assert result is False
    assert proxy_manager_instance.proxies == []

# --- Tests for Loading Proxies from File (.csv) ---

def create_mock_csv_content(data: List[List[str]]) -> str:
    """Helper to create a CSV string from a list of rows."""
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()

def test_load_proxies_from_csv_standard_format(proxy_manager_instance, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.csv")
    
    csv_data = [
        ['ip', 'port', 'https'],
        ['4.4.4.4', '8081', 'False'],
        ['5.5.5.5', '443', 'True'],
        ['6.6.6.6', '80', '1'], # Test '1' for True
        ['#7.7.7.7', '90', 'False'] # Should be skipped
    ]
    mock_content = create_mock_csv_content(csv_data)
    
    with patch("builtins.open", mock_open(read_data=mock_content)):
        result = proxy_manager_instance.load_proxies_from_file()

    assert result is True
    assert proxy_manager_instance.proxies == [
        "http://4.4.4.4:8081", 
        "https://5.5.5.5:443",
        "https://6.6.6.6:80"
    ]

def test_load_proxies_from_csv_simple_format_fallback(proxy_manager_instance, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.csv")
    
    # Simple CSV where header is missing or non-standard, triggering fallback
    csv_data = [
        ['http://8.8.8.8:8888'],
        ['9.9.9.9:9999'], # Should auto-add http://
        ['socks5://10.10.10.10:1010']
    ]
    mock_content = create_mock_csv_content(csv_data)
    
    with patch("builtins.open", mock_open(read_data=mock_content)):
        result = proxy_manager_instance.load_proxies_from_file()

    assert result is True
    assert proxy_manager_instance.proxies == [
        "http://8.8.8.8:8888",
        "http://9.9.9.9:9999",
        "socks5://10.10.10.10:1010"
    ]

def test_load_proxies_from_csv_removes_duplicates(proxy_manager_instance, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.csv")
    
    csv_data = [
        ['ip', 'port', 'https'],
        ['11.11.11.11', '80', 'False'],
        ['11.11.11.11', '80', 'False'], # Duplicate
        ['12.12.12.12', '443', 'True'],
    ]
    mock_content = create_mock_csv_content(csv_data)
    
    with patch("builtins.open", mock_open(read_data=mock_content)):
        proxy_manager_instance.load_proxies_from_file()

    assert proxy_manager_instance.proxies == [
        "http://11.11.11.11:80", 
        "https://12.12.12.12:443"
    ]

# --- Tests for Single Proxy Validation (Network Mocking) ---

@pytest.fixture
def mock_requests_get():
    """Patches requests.get and returns the mock object."""
    with patch('requests.get') as mock_get:
        yield mock_get

def create_mock_response(status_code: int) -> MagicMock:
    """Helper to create a mock response object."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    return mock_response

def test_validate_proxy_success(proxy_manager_instance, mock_requests_get):
    mock_requests_get.return_value = create_mock_response(200)
    
    proxy = "http://valid.proxy:8080"
    result = proxy_manager_instance.validate_proxy(proxy, timeout=5)
    
    assert result is True
    mock_requests_get.assert_called_once()
    assert mock_requests_get.call_args[1]['proxies'] == {'http': proxy, 'https': proxy}

def test_validate_proxy_failure_status_code(proxy_manager_instance, mock_requests_get):
    mock_requests_get.return_value = create_mock_response(404)
    
    result = proxy_manager_instance.validate_proxy("http://bad.status:80")
    assert result is False

def test_validate_proxy_connection_error(proxy_manager_instance, mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.ConnectionError
    
    result = proxy_manager_instance.validate_proxy("http://no.connect:80")
    assert result is False

def test_validate_proxy_timeout_error(proxy_manager_instance, mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.Timeout
    
    result = proxy_manager_instance.validate_proxy("http://slow.proxy:80")
    assert result is False

# --- Tests for Concurrent Validation (validate_all_proxies) ---

@patch('proxy_manager.ThreadPoolExecutor')
@patch('proxy_manager.Progress')
@patch('urllib3.disable_warnings')
def test_validate_all_proxies_logic(mock_disable_warnings, mock_progress, mock_executor, initialized_manager, mock_requests_get, mock_confirm):
    
    # 1. Setup Mock for concurrent execution environment
    
    # Mock Future results: 1st is success, 2nd is failure (404), 3rd is exception
    mock_future1 = MagicMock()
    mock_future1.result.return_value = True # Working
    mock_future2 = MagicMock()
    mock_future2.result.return_value = False # Failed (404)
    mock_future3 = MagicMock()
    mock_future3.result.side_effect = requests.exceptions.ProxyError # Failed (Exception)
    
    # Link futures back to their original proxies
    futures_map = {
        mock_future1: "http://1.1.1.1:80",
        mock_future2: "http://2.2.2.2:8080",
        mock_future3: "https://3.3.3.3:443"
    }
    
    # Mock the Executor to yield futures in the order of as_completed
    mock_executor.return_value.__enter__.return_value = MagicMock(
        submit=lambda func, *args: next(iter([f for f, p in futures_map.items() if p == args[0]]))
    )
    
    # Mock as_completed to return the futures in a known order
    with patch('proxy_manager.as_completed', return_value=futures_map.keys()):
        
        # Mock Confirmation to choose removal
        mock_confirm.ask.return_value = True 
        
        # 2. Execute
        initialized_manager.validate_all_proxies(max_workers=3, auto_remove=True)

    # 3. Assertions
    
    # Validation results:
    assert len(initialized_manager.working_proxies) == 1
    assert "http://1.1.1.1:80" in initialized_manager.working_proxies
    
    assert len(initialized_manager.failed_proxies) == 2
    assert "http://2.2.2.2:8080" in initialized_manager.failed_proxies
    assert "https://3.3.3.3:443" in initialized_manager.failed_proxies
    
    # Auto-removal was confirmed and executed:
    assert initialized_manager.proxies == initialized_manager.working_proxies
    mock_confirm.ask.assert_called_once()
    
# --- Tests for Summary and Removal ---

def test_get_summary(initialized_manager):
    # Manually populate working/failed proxies for test
    initialized_manager.working_proxies = ["p1", "p3"]
    initialized_manager.failed_proxies = ["p2"]
    
    summary = initialized_manager.get_summary()
    
    assert summary['total_proxies'] == 3
    assert summary['working_proxies'] == 2
    assert summary['failed_proxies'] == 1
    assert summary['success_rate'] == pytest.approx(66.666, 0.001)

@patch('proxy_manager.ProxyManager._save_proxies_to_file')
def test_remove_dead_proxies_success(mock_save_to_file, initialized_manager):
    initial_proxies = ["p1", "p2", "p3", "p4"]
    initialized_manager.proxies = initial_proxies.copy()
    initialized_manager.working_proxies = ["p1", "p4"]
    initialized_manager.failed_proxies = ["p2", "p3"]
    
    initialized_manager.remove_dead_proxies()
    
    assert initialized_manager.proxies == ["p1", "p4"]
    mock_save_to_file.assert_called_once()

# --- Tests for Saving Proxies to File ---

def test_save_proxies_to_txt_file(initialized_manager, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.txt")
    initialized_manager.proxies = ["http://a:1", "https://b:2"]
    
    m = mock_open()
    with patch("builtins.open", m):
        initialized_manager._save_proxies_to_file()

    m.assert_called_once_with(Path("proxies.txt"), 'w', encoding='utf-8')
    handle = m()
    handle.write.assert_has_calls([
        call("http://a:1\n"), 
        call("https://b:2\n")
    ])

def test_save_proxies_to_csv_file(initialized_manager, mock_path_exists):
    mock_path_exists.side_effect = lambda x: x == Path("proxies.csv")
    initialized_manager.proxies = ["http://a:1", "https://b:2", "socks5://c:3"]
    
    m = mock_open()
    with patch("builtins.open", m):
        initialized_manager._save_proxies_to_file()

    m.assert_called_once_with(Path("proxies.csv"), 'w', encoding='utf-8', newline='')
    
    # Check what was written to the file (requires checking the CSV writer)
    handle = m()
    written_data = "".join(c for c in handle.write.call_args_list[0][0][0] if c != '\r').split('\n')
    
    # Check headers and first two working proxies
    assert written_data[0] == 'ip,port,country,https,scraped_from,status,speed,location,last_checked'
    # http://a:1
    assert written_data[1].startswith('a,1,,False,Validated,Working')
    # https://b:2
    assert written_data[2].startswith('b,2,,True,Validated,Working')
    # socks5://c:3 is also attempted to be saved, but parsing logic is limited, 
    # ensuring at least the first two common formats are correctly saved back.
