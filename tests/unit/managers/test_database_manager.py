import pytest
import sqlite3
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from typing import List

# To enable importing, we assume database_manager.py is in the Python path
# In a standard project setup: from database_manager import DatabaseManager

# --- Mock Objects for SQLite and Rich ---

# Mock the rich console to suppress terminal output during tests
class MockConsole:
    def print(self, *args, **kwargs):
        pass

# Mock the sqlite3.Row object behavior
class MockRow:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def keys(self):
        return list(self._data.keys())

# --- Fixtures ---

@pytest.fixture(scope="module", autouse=True)
def mock_rich_console():
    """Patches the rich console globally to prevent test output."""
    # We need to import the class from the source file to patch it correctly
    with patch('database_manager.console', MockConsole()):
        yield

@pytest.fixture
def mock_sqlite_cursor():
    """Returns a mock cursor object."""
    cursor = MagicMock(spec=sqlite3.Cursor)
    # Mocking lastrowid for get_last_insert_id test
    cursor.lastrowid = 42 
    return cursor

@pytest.fixture
def mock_sqlite_connection(mock_sqlite_cursor):
    """Returns a mock connection object, linked to the mock cursor."""
    connection = MagicMock(spec=sqlite3.Connection)
    connection.cursor.return_value = mock_sqlite_cursor
    return connection

@pytest.fixture
def mock_sqlite3_connect(mock_sqlite_connection):
    """Patches sqlite3.connect to return the mock connection."""
    with patch('sqlite3.connect', return_value=mock_sqlite_connection) as mock_connect:
        yield mock_connect

@pytest.fixture
def db_manager():
    """Provides an uninitialized DatabaseManager instance."""
    from database_manager import DatabaseManager
    # Use a dummy path for Path object creation
    return DatabaseManager(db_path=":memory:")

@pytest.fixture
def connected_db_manager(db_manager, mock_sqlite3_connect):
    """Provides a DatabaseManager instance that has successfully called connect()."""
    db_manager.connect()
    # The internal connection object is the mock connection
    return db_manager

# --- Tests for Connection and Disconnection ---

def test_init_sets_db_path():
    """Test initialization sets the correct Path object."""
    from database_manager import DatabaseManager
    manager = DatabaseManager(db_path="test.db")
    assert manager.db_path == Path("test.db")
    assert manager.connection is None

def test_connect_success(db_manager, mock_sqlite3_connect, mock_sqlite_connection):
    """Test successful database connection."""
    result = db_manager.connect()
    
    # Assert sqlite3.connect was called with the correct path
    mock_sqlite3_connect.assert_called_once_with(db_manager.db_path)
    
    # Assert row_factory was set
    assert db_manager.connection.row_factory == sqlite3.Row
    assert result is True

@patch('sqlite3.connect', side_effect=sqlite3.Error("Connection Failed"))
def test_connect_failure(mock_connect, db_manager):
    """Test connection failure handling."""
    result = db_manager.connect()
    
    assert db_manager.connection is None
    assert result is False

def test_disconnect(connected_db_manager, mock_sqlite_connection):
    """Test disconnecting closes the connection."""
    connected_db_manager.disconnect()
    
    mock_sqlite_connection.close.assert_called_once()
    assert connected_db_manager.connection is None

def test_disconnect_when_not_connected(db_manager):
    """Test disconnecting when no connection is active does nothing."""
    # Should not raise an error
    db_manager.disconnect()
    assert db_manager.connection is None

# --- Tests for create_tables ---

def test_create_tables_success(connected_db_manager, mock_sqlite_cursor):
    """Test successful table creation."""
    result = connected_db_manager.create_tables()
    
    # Check that execute was called for each table and index
    # (Checking the exact number of calls is a good proxy for all DDL)
    # 5 Tables + 5 Indexes = 10 total execute calls
    assert mock_sqlite_cursor.execute.call_count == 10
    
    # Check for a specific table creation query (sample check)
    channel_query = mock_sqlite_cursor.execute.call_args_list[0][0][0].strip()
    assert channel_query.startswith("CREATE TABLE IF NOT EXISTS channels")
    
    connected_db_manager.connection.commit.assert_called_once()
    assert result is True

@patch('database_manager.DatabaseManager.connect', return_value=True)
def test_create_tables_calls_connect_if_not_connected(mock_connect_method, db_manager):
    """Test create_tables calls connect if connection is None."""
    db_manager.create_tables()
    mock_connect_method.assert_called_once()

def test_create_tables_failure(connected_db_manager, mock_sqlite_cursor):
    """Test table creation failure handling."""
    # Simulate a failure on the first execute call
    mock_sqlite_cursor.execute.side_effect = sqlite3.Error("DDL Failure")
    
    result = connected_db_manager.create_tables()
    
    # Connection should try to rollback on error
    connected_db_manager.connection.rollback.assert_called_once()
    assert result is False

# --- Tests for DML/DQL Operations ---

def test_execute_query_success(connected_db_manager, mock_sqlite_cursor):
    """Test successful non-returning query execution."""
    query = "INSERT INTO test VALUES (?, ?)"
    params = ("val1", 123)
    result = connected_db_manager.execute_query(query, params)
    
    mock_sqlite_cursor.execute.assert_called_once_with(query, params)
    connected_db_manager.connection.commit.assert_called_once()
    assert connected_db_manager.connection.rollback.call_count == 0
    assert result is True

def test_execute_query_failure(connected_db_manager, mock_sqlite_cursor):
    """Test query execution failure handling (should rollback)."""
    mock_sqlite_cursor.execute.side_effect = sqlite3.Error("DML Failure")
    
    result = connected_db_manager.execute_query("DELETE FROM test")
    
    connected_db_manager.connection.rollback.assert_called_once()
    connected_db_manager.connection.commit.call_count == 0
    assert result is False

def test_fetch_one_success(connected_db_manager, mock_sqlite_cursor):
    """Test single row fetch success."""
    mock_sqlite_cursor.fetchone.return_value = MockRow({"id": 1, "name": "test"})
    query = "SELECT * FROM test WHERE id=?"
    params = (1,)
    
    result = connected_db_manager.fetch_one(query, params)
    
    mock_sqlite_cursor.execute.assert_called_once_with(query, params)
    assert result['id'] == 1
    assert result['name'] == "test"

def test_fetch_one_failure(connected_db_manager, mock_sqlite_cursor):
    """Test single row fetch failure."""
    mock_sqlite_cursor.execute.side_effect = sqlite3.Error("DQL Failure")
    
    result = connected_db_manager.fetch_one("SELECT * FROM test")
    
    assert result is None

def test_fetch_all_success(connected_db_manager, mock_sqlite_cursor):
    """Test multiple row fetch success."""
    mock_data = [
        MockRow({"id": 1}), 
        MockRow({"id": 2})
    ]
    mock_sqlite_cursor.fetchall.return_value = mock_data
    query = "SELECT * FROM test"
    
    result: List[MockRow] = connected_db_manager.fetch_all(query)
    
    mock_sqlite_cursor.execute.assert_called_once_with(query, ())
    assert len(result) == 2
    assert result[0]['id'] == 1
    assert result[1]['id'] == 2

def test_fetch_all_failure(connected_db_manager, mock_sqlite_cursor):
    """Test multiple row fetch failure."""
    mock_sqlite_cursor.execute.side_effect = sqlite3.Error("DQL Failure")
    
    result = connected_db_manager.fetch_all("SELECT * FROM test")
    
    assert result == []

def test_get_last_insert_id_success(connected_db_manager, mock_sqlite_cursor):
    """Test retrieving the last inserted row ID."""
    result = connected_db_manager.get_last_insert_id()
    
    assert result == 42 # Mocked value

def test_get_last_insert_id_failure(connected_db_manager, mock_sqlite_cursor):
    """Test error handling when getting last row ID."""
    # lastrowid raises an AttributeError if called at the wrong time, but we 
    # mock a sqlite3.Error here for testing the specific handler.
    mock_sqlite_cursor.lastrowid = property(lambda self: (_ for _ in ()).throw(sqlite3.Error))
    
    result = connected_db_manager.get_last_insert_id()
    
    assert result is None

# --- Tests for Transaction Management ---

def test_begin_transaction(connected_db_manager, mock_sqlite_connection):
    """Test begin_transaction executes the BEGIN command."""
    connected_db_manager.begin_transaction()
    
    mock_sqlite_connection.execute.assert_called_once_with("BEGIN")

def test_commit(connected_db_manager, mock_sqlite_connection):
    """Test commit calls connection.commit()."""
    connected_db_manager.commit()
    
    mock_sqlite_connection.commit.assert_called_once()

def test_rollback(connected_db_manager, mock_sqlite_connection):
    """Test rollback calls connection.rollback()."""
    connected_db_manager.rollback()
    
    mock_sqlite_connection.rollback.assert_called_once()

# Test the safety net connection calls for CRUD when not connected
@patch('database_manager.DatabaseManager.connect', return_value=True)
def test_crud_calls_connect_if_not_connected(mock_connect_method, db_manager, mock_sqlite_cursor):
    """Test that DML/DQL methods call connect() if not already connected."""
    # Manager is not connected by default
    db_manager.execute_query("DUMMY")
    db_manager.fetch_one("DUMMY")
    db_manager.fetch_all("DUMMY")
    
    # Connect should have been called three times
    assert mock_connect_method.call_count == 3
