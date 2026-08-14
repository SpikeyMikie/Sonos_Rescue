"""Database module for Sonos Rescue."""

import sqlite3
import threading


class ArtworkDatabase:
    """
    Simple SQLite cache for artwork bytes.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.Lock()
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.init_artwork_db()

    def init_artwork_db(self) -> None:
        with self._lock:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS 
                artwork (
                url TEXT PRIMARY KEY,
                data BLOB NOT NULL
            )
            """)
            self.connection.commit()

    def get_artwork_data(self, url: str) -> bytes | None:
        """Retrieve artwork data for a given URL."""
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT data FROM artwork WHERE url = ?",
                (url,),
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def insert_artwork_data(self, url: str, data: bytes) -> None:
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO artwork(url, data) VALUES(?, ?)",
                (url, data),
            )
            self.connection.commit()

    def delete_artwork_data(self, url: str) -> None:
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM artwork WHERE url = ?",
                (url,),
            )
            self.connection.commit()

    def close(self) -> None:
        with self._lock:
            self.connection.close()
