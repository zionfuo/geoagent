"""SQLite database connection manager."""
import threading
from pathlib import Path
from typing import Optional
import sqlite3


class Database:
    """Singleton SQLite connection manager with thread-local connections."""
    _instance: Optional["Database"] = None
    _local = threading.local()

    DEFAULT_PATH = Path.home() / ".geoagent" / "geoagent.db"

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "Database":
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else self.DEFAULT_PATH

    def get_connection(self) -> sqlite3.Connection:
        # Get connection for current thread only
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")
        return self._local.conn

    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
        Database._instance = None

    def reset(self):
        """Reset singleton for testing."""
        self.close()
