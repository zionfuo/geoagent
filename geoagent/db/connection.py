"""SQLite database connection manager."""
from pathlib import Path
from typing import Optional
import sqlite3


class Database:
    """Singleton SQLite connection manager."""
    _instance: Optional["Database"] = None
    _conn: Optional[sqlite3.Connection] = None

    DEFAULT_PATH = Path.home() / ".geoagent" / "geoagent.db"

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "Database":
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else self.DEFAULT_PATH
        self._conn = None

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            Database._instance = None

    def reset(self):
        """Reset singleton for testing."""
        self.close()
