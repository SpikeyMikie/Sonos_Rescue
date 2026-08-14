"""Database module for Sonos Rescue."""

import sqlite3


class ArtworkDatabase:
    """
    Class to manage the artwork database.
    This class provides methods to initialize the database, insert, retrieve,
    and delete artwork data, as well as to close the database connection.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.connection = sqlite3.connect(db_path)
        self.init_artwork_db()

    def init_artwork_db(self) -> None:
        """Initialize the artwork database."""
        self.connection.execute("""
        CREATE TABLE IF NOT EXISTS artwork (
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
        """Insert or replace artwork data for a given URL."""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO artwork(url, data) VALUES(?, ?)",
            (url, data),
        )
        self.connection.commit()

    def delete_artwork_data(self, url: str) -> None:
        """Delete artwork data for a given URL."""
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM artwork WHERE url = ?",
            (url,),
        )
        self.connection.commit()

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()


artwork_db = ArtworkDatabase(":memory:")  # Initialize the artwork database in memory

cursor = artwork_db.connection.cursor()


# prints for debug
print("Database tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

print("Artwork table schema:")
cursor.execute("PRAGMA table_info(artwork);")
columns = cursor.fetchall()
for column in columns:
    print(column)

print("Artwork table contents:")
cursor.execute("SELECT * FROM artwork;")
rows = cursor.fetchall()
if not rows:
    print("No rows in artwork table.")
else:
    for row in rows:
        print(row)
