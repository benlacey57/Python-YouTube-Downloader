"""Database abstraction layer"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Tuple
from contextlib import contextmanager


class DatabaseConnection(ABC):
    """Abstract database connection"""
    
    @abstractmethod
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Tuple = ()) -> Any:
        """Execute query and return cursor"""
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """Fetch single row"""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict]:
        """Fetch all rows"""
        pass
    
    @abstractmethod
    def insert(self, query: str, params: Tuple = ()) -> int:
        """Insert and return last row ID"""
        pass
    
    @abstractmethod
    def update(self, query: str, params: Tuple = ()) -> int:
        """Update and return affected rows"""
        pass
    
    @abstractmethod
    def delete(self, query: str, params: Tuple = ()) -> int:
        """Delete and return affected rows"""
        pass
    
    @abstractmethod
    def init_schema(self):
        """Initialize database schema"""
        pass
