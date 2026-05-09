"""Admin and site settings for geoagent."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SiteSetting:
    id: Optional[int] = None
    setting_key: str = ""
    setting_value: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SiteSettings:
    """Key-value store for site settings."""

    def __init__(self, db):
        self.db = db

    def _conn(self):
        return self.db.get_connection()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value FROM site_settings WHERE setting_key = ?", (key,))
        row = cursor.fetchone()
        return row["setting_value"] if row else default

    def set(self, key: str, value: str):
        """Set a setting value (upsert)."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO site_settings (setting_key, setting_value, created_at, updated_at)
               VALUES (?, ?, datetime('now'), datetime('now'))
               ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?, updated_at = datetime('now')""",
            (key, value, value),
        )
        conn.commit()

    def delete(self, key: str) -> bool:
        """Delete a setting."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM site_settings WHERE setting_key = ?", (key,))
        conn.commit()
        return cursor.rowcount > 0
