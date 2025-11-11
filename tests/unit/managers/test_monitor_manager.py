import pytest
import threading
import time
from unittest.mock import MagicMock, patch, call, NonCallableMock
from datetime import datetime
from typing import List, Tuple, Any

# Mock the external dependencies for isolation
# In a real environment, you would import them from your project structure

# Mock the Channel model class
class MockChannel:
    """Mock class to stand in for the models.channel.Channel dataclass."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = kwargs.get('id', None)
        self.url = kwargs.get('url', 'http://test.url')
        self.check_interval_minutes = kwargs.get('check_interval_minutes', 60)

    @classmethod
    def from_row(cls, row_tuple: Tuple[Any, ...]):
        """Mock method for converting a database row into a Channel object."""
        # Assume the first element in the tuple is the channel ID for simplicity
        return cls(id=row_tuple[0])

    def prepare_for_insert(self):
        """Mock method to return prepared data for INSERT."""
        return ('insert_data',)

    def prepare_for_update(self):
        """Mock method to return prepared data for UPDATE."""
        return ('update_data', self.id)

# Mock the rich console to suppress terminal output during tests
class MockConsole:
    def print(self, *args, **kwargs):
        pass

# --- Fixtures ---

@pytest.fixture(scope="module", autouse=True)
def mock_rich_console():
    """Patches the rich console globally to prevent test output."""
    with patch('monitor_manager.console', MockConsole()):
        yield

@pytest.fixture
def mock_db_manager():
    """Provides a mock DatabaseManager instance."""
    # We use a NonCallableMock to ensure methods are not accidentally called
    db_manager = NonCallableMock(spec_set=['fetch_one', 'fetch_all', 'execute_query', 'get_last_insert_id'])
    
    # Configure defaults for fetch methods
    db_manager.fetch_one.return_value = None
    db_manager.fetch_all.return_value = []
    db_manager.get_last_insert_id.return_value = 1
    
    return db_manager

@pytest.fixture
def monitor_manager(mock_db_manager):
    """Provides a MonitorManager instance initialized with the mock DB."""
    # Patch the Channel import
    with patch('monitor_manager.Channel', new=MockChannel):
        from monitor_manager import MonitorManager
        return MonitorManager(db_manager=mock_db_manager)

# --- Tests for Basic CRUD Operations ---

def test_init(monitor_manager, mock_db_manager):
    """Test initialization."""
    assert monitor_manager.db is mock_db_manager
    assert monitor_manager.is_running is False
    assert monitor_manager.monitor_thread is None

# --- Test add_channel (Update Path) ---

def test_add_channel_updates_existing(monitor_manager, mock_db_manager):
    """Test adding a channel that already exists should trigger an UPDATE."""
    
    # Setup mock to simulate existing channel
    mock_db_manager.fetch_one.return_value = (50,)
    channel = MockChannel(id=50)

    result_id = monitor_manager.add_channel(channel)
    
    # 1. Verify check for existing channel was called
    mock_db_manager.fetch_one.assert_called_once_with(
        "SELECT id FROM channels WHERE url = ?", 
        (channel.url,)
    )
    
    # 2. Verify UPDATE query was executed
    mock_db_manager.execute_query.assert_called_once()
    assert mock_db_manager.execute_query.call_args[0][0].strip().startswith("UPDATE channels SET")
    assert mock_db_manager.execute_query.call_args[0][1] == channel.prepare_for_update()
    
    # 3. Verify it returns the existing ID
    assert result_id == 50
    # 4. Verify INSERT was NOT called
    mock_db_manager.get_last_insert_id.assert_not_called()

# --- Test add_channel (Insert Path) ---

def test_add_channel_inserts_new(monitor_manager, mock_db_manager):
    """Test adding a new channel should trigger an INSERT and return the new ID."""
    
    # Setup mock to simulate new channel (fetch_one returns None by default)
    channel = MockChannel(id=None)
    mock_db_manager.get_last_insert_id.return_value = 101

    result_id = monitor_manager.add_channel(channel)
    
    # 1. Verify check for existing channel was called
    mock_db_manager.fetch_one.assert_called_once()
    
    # 2. Verify INSERT query was executed
    mock_db_manager.execute_query.assert_called_once()
    assert mock_db_manager.execute_query.call_args[0][0].strip().startswith("INSERT INTO channels")
    assert mock_db_manager.execute_query.call_args[0][1] == channel.prepare_for_insert()
    
    # 3. Verify last insert ID was fetched
    mock_db_manager.get_last_insert_id.assert_called_once()
    
    # 4. Verify it returns the new ID
    assert result_id == 101

# --- Test remove_channel ---

def test_remove_channel(monitor_manager, mock_db_manager):
    """Test removing a channel calls the correct DELETE query."""
    channel_id = 99
    
    monitor_manager.remove_channel(channel_id)
    
    mock_db_manager.execute_query.assert_called_once_with(
        "DELETE FROM channels WHERE id = ?",
        (channel_id,)
    )

# --- Test update_channel ---

def test_update_channel(monitor_manager, mock_db_manager):
    """Test updating a channel calls the correct UPDATE query."""
    channel = MockChannel(id=12)
    
    monitor_manager.update_channel(channel)
    
    mock_db_manager.execute_query.assert_called_once()
    assert mock_db_manager.execute_query.call_args[0][0].strip().startswith("UPDATE channels SET")
    assert mock_db_manager.execute_query.call_args[0][1] == channel.prepare_for_update()

# --- Test Getters ---

def test_get_monitored_channels(monitor_manager, mock_db_manager):
    """Test retrieving only monitored and enabled channels."""
    mock_db_manager.fetch_all.return_value = [(1,), (2,)] # Mock two rows
    
    channels = monitor_manager.get_monitored_channels()
    
    mock_db_manager.fetch_all.assert_called_once_with(
        "SELECT * FROM channels WHERE is_monitored = 1 AND enabled = 1"
    )
    assert len(channels) == 2
    assert isinstance(channels[0], MockChannel)
    assert channels[0].id == 1
    assert channels[1].id == 2

def test_get_all_channels(monitor_manager, mock_db_manager):
    """Test retrieving all channels."""
    mock_db_manager.fetch_all.return_value = [(10,), (11,)]
    
    channels = monitor_manager.get_all_channels()
    
    mock_db_manager.fetch_all.assert_called_once_with(
        "SELECT * FROM channels ORDER BY created_at DESC"
    )
    assert len(channels) == 2

def test_get_channel_by_url_found(monitor_manager, mock_db_manager):
    """Test retrieving a channel by URL when found."""
    mock_db_manager.fetch_one.return_value = (33,)
    test_url = "http://channel.xyz"
    
    channel = monitor_manager.get_channel_by_url(test_url)
    
    mock_db_manager.fetch_one.assert_called_once_with(
        "SELECT * FROM channels WHERE url = ?",
        (test_url,)
    )
    assert isinstance(channel, MockChannel)
    assert channel.id == 33

def test_get_channel_by_url_not_found(monitor_manager, mock_db_manager):
    """Test retrieving a channel by URL when not found."""
    mock_db_manager.fetch_one.return_value = None
    
    channel = monitor_manager.get_channel_by_url("missing_url")
    
    assert channel is None

# --- Tests for Monitoring Logic (Threading/Time) ---

@patch('monitor_manager.threading.Thread')
@patch('monitor_manager.time.sleep')
def test_start_monitoring_starts_thread(mock_sleep, mock_thread, monitor_manager):
    """Test start_monitoring initializes and starts the thread."""
    mock_callback = MagicMock()
    
    monitor_manager.start_monitoring(mock_callback)
    
    # Verify is_running is set
    assert monitor_manager.is_running is True
    
    # Verify Thread was created with the monitor_loop target and started
    mock_thread.assert_called_once()
    assert mock_thread.call_args[1]['daemon'] is True
    assert monitor_manager.monitor_thread is not None
    monitor_manager.monitor_thread.start.assert_called_once()

@patch('monitor_manager.threading.Thread', MagicMock) # Mocking thread to prevent actual threading
@patch('monitor_manager.time.sleep')
def test_start_monitoring_already_running(mock_sleep, monitor_manager):
    """Test calling start_monitoring when already running does nothing."""
    mock_callback = MagicMock()
    monitor_manager.is_running = True
    
    monitor_manager.start_monitoring(mock_callback)
    
    # Thread should not be created if is_running is True
    assert monitor_manager.monitor_thread is None

def test_stop_monitoring(monitor_manager):
    """Test stop_monitoring sets flag and joins thread."""
    # Simulate a running thread
    mock_thread = MagicMock(spec=threading.Thread)
    monitor_manager.monitor_thread = mock_thread
    monitor_manager.is_running = True
    
    monitor_manager.stop_monitoring()
    
    assert monitor_manager.is_running is False
    mock_thread.join.assert_called_once_with(timeout=5)

# --- Test the monitor_loop internal logic ---

@patch('monitor_manager.MonitorManager.get_monitored_channels')
@patch('monitor_manager.time.sleep')
@patch('monitor_manager.datetime')
def test_monitor_loop_with_channels(mock_datetime, mock_sleep, mock_get_channels, monitor_manager):
    """Test monitor_loop execution with channels, checking callback and sleep time."""
    
    # Setup: 2 channels with different check intervals
    channel_c = MockChannel(check_interval_minutes=10)
    channel_a = MockChannel(check_interval_minutes=5)
    mock_get_channels.return_value = [channel_a, channel_c]
    
    mock_callback = MagicMock()
    monitor_manager.is_running = True
    
    # Simulate one iteration of the loop by using side_effect to stop it
    def stop_loop_after_one_run(*args, **kwargs):
        monitor_manager.is_running = False
        
    mock_sleep.side_effect = stop_loop_after_one_run
    
    # Execute the internal loop function directly
    with patch('monitor_manager.console', MockConsole()): # Ensure console is mocked during loop execution
        monitor_manager._monitor_loop = lambda: monitor_manager.start_monitoring(mock_callback)
        
        # We need to run the target function of the thread, not the start method.
        # Since the start_monitoring creates a thread, we'll extract the loop function.
        loop_target = monitor_manager.start_monitoring.__globals__['monitor_loop']
        loop_target()

    # 1. Callback should be called once with the channels
    mock_callback.assert_called_once_with([channel_a, channel_c])
    
    # 2. Sleep should be called with the minimum interval (5 minutes)
    mock_sleep.assert_called_once_with(5 * 60)
    
    # 3. get_monitored_channels should be called once
    mock_get_channels.assert_called_once()

@patch('monitor_manager.MonitorManager.get_monitored_channels')
@patch('monitor_manager.time.sleep')
def test_monitor_loop_no_channels(mock_sleep, mock_get_channels, monitor_manager):
    """Test monitor_loop sleep time when no channels are returned."""
    mock_get_channels.return_value = [] # No channels
    mock_callback = MagicMock()
    monitor_manager.is_running = True
    
    # Simulate one iteration of the loop by using side_effect to stop it
    def stop_loop_after_one_run(*args, **kwargs):
        monitor_manager.is_running = False
        
    mock_sleep.side_effect = stop_loop_after_one_run
    
    # Execute the internal loop function directly
    loop_target = monitor_manager.start_monitoring.__globals__['monitor_loop']
    with patch('monitor_manager.console', MockConsole()):
        loop_target()
    
    # Sleep should be called with the default 300 seconds (5 minutes)
    mock_sleep.assert_called_once_with(300)
    mock_callback.assert_not_called()

@patch('monitor_manager.MonitorManager.get_monitored_channels')
@patch('monitor_manager.time.sleep')
def test_monitor_loop_exception_handling(mock_sleep, mock_get_channels, monitor_manager):
    """Test monitor_loop handles exceptions and sleeps for 60s."""
    
    # Setup: make get_monitored_channels raise an exception
    mock_get_channels.side_effect = Exception("DB Error")
    mock_callback = MagicMock()
    monitor_manager.is_running = True
    
    # Simulate one iteration of the loop by using side_effect to stop it
    def stop_loop_after_one_run(*args, **kwargs):
        monitor_manager.is_running = False
        
    mock_sleep.side_effect = stop_loop_after_one_run
    
    # Execute the internal loop function directly
    loop_target = monitor_manager.start_monitoring.__globals__['monitor_loop']
    with patch('monitor_manager.console', MockConsole()):
        loop_target()
    
    # Sleep should be called with the error interval (60 seconds)
    mock_sleep.assert_called_once_with(60)
    mock_callback.assert_not_called()
