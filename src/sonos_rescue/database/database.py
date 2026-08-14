"""Database module for Sonos Rescue."""

import sqlite3


class ArtworkDatabase:
    """
    Simple SQLite cache for artwork bytes.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.connection = sqlite3.connect(db_path)
        self.init_artwork_db()

    def init_artwork_db(self) -> None:
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
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT data FROM artwork WHERE url = ?",
            (url,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def insert_artwork_data(self, url: str, data: bytes) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO artwork(url, data) VALUES(?, ?)",
            (url, data),
        )
        self.connection.commit()

    def delete_artwork_data(self, url: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM artwork WHERE url = ?",
            (url,),
        )
        self.connection.commit()

    def close(self) -> None:

        self.connection.close()
