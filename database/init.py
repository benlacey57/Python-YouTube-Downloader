"""Database module"""
from database.base import DatabaseConnection
from database.sqlite_connection import SQLiteConnection
from database.mysql_connection import MySQLConnection


def get_database_connection(db_type: str = "sqlite", **kwargs) -> DatabaseConnection:
    """
    Get database connection based on type
    
    Args:
        db_type: Database type ('sqlite' or 'mysql')
        **kwargs: Database-specific configuration
    
    Returns:
        DatabaseConnection instance
    """
    if db_type == "sqlite":
        db_path = kwargs.get('db_path', 'data/downloader.db')
        return SQLiteConnection(db_path)
    elif db_type == "mysql":
        return MySQLConnection(
            host=kwargs.get('host', 'localhost'),
            port=kwargs.get('port', 3306),
            database=kwargs.get('database', 'downloader'),
            user=kwargs.get('user', 'root'),
            password=kwargs.get('password', '')
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
