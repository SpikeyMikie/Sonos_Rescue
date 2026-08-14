# tests/database/test_database.py
"""Tests for the database module."""

import pytest
from sonos_rescue.database.database import ArtworkDatabase

# Test the ArtworkDatabase class


@pytest.fixture
def artwork_db():
    """Provide a fresh in-memory artwork database for each test."""
    db = ArtworkDatabase(":memory:")
    yield db
    db.close()


def test_init_artwork_database_creates_table(artwork_db: ArtworkDatabase):
    """Test that the artwork table is created successfully."""
    cursor = artwork_db.connection.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='artwork';"
    )
    table = cursor.fetchone()
    assert table is not None, "Artwork table should be created."


def test_insert_and_get_artwork_data(artwork_db: ArtworkDatabase):
    """Test inserting and retrieving artwork data."""

    url = "http://example.com/artwork.jpg"
    data = b"fake_image_data"

    artwork_db.insert_artwork_data(url, data)

    retrieved_data = artwork_db.get_artwork_data(url)

    assert retrieved_data == data


def test_get_artwork_data_nonexistent_url(artwork_db: ArtworkDatabase):
    """Retrieved data should be None for nonexistent URL."""
    url = "http://example.com/nonexistent_artwork.jpg"
    retrieved_data = artwork_db.get_artwork_data(url)
    assert retrieved_data is None


def test_insert_artwork_data_replaces_existing(artwork_db: ArtworkDatabase):
    """Retrieved data should match the new inserted data."""
    url = "http://example.com/artwork_replace.jpg"
    original_data = b"original_image_data"
    new_data = b"new_image_data"

    # Insert original artwork data
    artwork_db.insert_artwork_data(url, original_data)

    # Insert new artwork data for the same URL
    artwork_db.insert_artwork_data(url, new_data)

    # Retrieve artwork data and check if it matches the new data
    retrieved_data = artwork_db.get_artwork_data(url)
    assert retrieved_data == new_data


def test_delete_artwork_data(artwork_db: ArtworkDatabase):
    """Retrieved data should be None after deletion."""
    url = "http://example.com/artwork_to_delete.jpg"
    data = b"fake_image_data_to_delete"

    artwork_db.insert_artwork_data(url, data)

    artwork_db.delete_artwork_data(url)

    # Try to retrieve deleted artwork data
    retrieved_data = artwork_db.get_artwork_data(url)
    assert retrieved_data is None


def test_close_database_connection(artwork_db: ArtworkDatabase):
    """Should close without errors"""
    artwork_db.close()
