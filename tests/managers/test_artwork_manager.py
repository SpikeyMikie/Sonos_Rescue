from pathlib import Path
import pytest
from types import SimpleNamespace
from typing import Any, Literal, cast
from sonos_rescue.database.database import ArtworkDatabase
import sonos_rescue.managers.artwork_manager as artwork_mod


@pytest.fixture
def album_label_stub():
    class AlbumLabel:
        def __init__(self) -> None:
            self.pixmap: Any | None = None
            self.width: int | None = None
            self.height: int | None = None
            self.scaled_contents: bool | None = None
            self.horizontal_policy: Any | None = None
            self.vertical_policy: Any | None = None
            self.setMinimum_size: tuple[int, int] | None = None
            self.setMaximum_size: tuple[int, int] | None = None

        def setPixmap(self, pixmap: Any) -> None:
            self.pixmap = pixmap

        def setFixedSize(self, width: int, height: int) -> None:
            self.width = width
            self.height = height

        def setScaledContents(self, value: bool) -> None:
            self.scaled_contents = value

        def setMinimumSize(self, width: int, height: int) -> None:
            self.setMinimum_size = (width, height)

        def setMaximumSize(self, width: int, height: int) -> None:
            self.setMaximum_size = (width, height)

        def setSizePolicy(self, horizontal: Any, vertical: Any) -> None:
            self.horizontal_policy = horizontal
            self.vertical_policy = vertical

    return AlbumLabel()


@pytest.fixture
def fake_pixmap_class():
    class FakePixmap:
        def __init__(self):
            self.data = None

        def loadFromData(self, d: bytes):
            self.data = d

        def scaled(
            self,
            width: int,
            height: int,
            aspect_ratio_mode: object,
            transformation_mode: object,
        ):
            assert width == 500
            assert height == 500
            return self

    return FakePixmap


@pytest.fixture
def fake_image_factory():
    class FakeImage:
        size = (400, 400)

        def resize(
            self,
            size: tuple[int, int],
            method: object = None,
            box: object = None,
        ):
            return FakeResizedImage()

    class FakeResizedImage:
        def save(self, buffer: Any, format: str) -> None:
            buffer.write(b"png-bytes")

    def make_fake_image() -> FakeImage:
        return FakeImage()

    return make_fake_image, FakeResizedImage


def test_get_album_art_from_file_returns_data_and_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Validate `get_album_art_from_file` extracts APIC frame data from
    an MP3 file and returns `None` when MP3 parsing fails.

    The test replaces `MP3` with a fake that provides an APIC-like tag
    and then with a callable that raises to exercise the exception
    handling path.
    """

    mod = artwork_mod

    # mock MP3 to return tags containing an APIC-like object
    class Tag:
        FrameID = "APIC"
        type = 3
        data = b"ART"

    class FakeMP3:
        def __init__(self, path: str, ID3: object = None):
            self.tags = {"APIC": Tag()}

    monkeypatch.setattr(artwork_mod, "MP3", FakeMP3)

    app = mod.ArtworkManager.__new__(mod.ArtworkManager)
    data = mod.ArtworkManager.get_album_art_from_file(app, str(tmp_path / "fake.mp3"))
    assert data == b"ART"

    # now MP3 raises
    def bad_mp3(*args: object, **kwargs: object) -> None:
        raise Exception("bad")

    monkeypatch.setattr(artwork_mod, "MP3", bad_mp3)
    data2 = mod.ArtworkManager.get_album_art_from_file(app, str(tmp_path / "fake.mp3"))
    assert data2 is None


def test_set_album_art_scales_to_fixed_square_size(album_label_stub: Any):
    """`set_album_art` should produce a consistent square 500x500 render."""
    mod = artwork_mod
    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))

    class FakePixmap:
        def __init__(self):
            self.data = None

        def loadFromData(self, d: bytes):
            self.data = d

        def scaled(self, *args: object, **kwargs: object) -> "FakePixmap":
            return self

    pixmap = FakePixmap()
    manager.set_album_art(album_label_stub, cast(Any, pixmap))

    assert album_label_stub.width == 500
    assert album_label_stub.height == 500
    assert album_label_stub.scaled_contents is False


def test_load_art_uses_memory_cache(
    monkeypatch: pytest.MonkeyPatch, album_label_stub: Any
):
    """
    Test that `load_art` uses the in-memory cache when the artwork URL is already cached.
    This test creates a minimal `SonosApp`-like object with `current` set,
    and verifies that the cached artwork is used instead of fetching it again.
    """
    mod = artwork_mod

    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))
    url = "http://fake-url.test/album.jpg"

    class FakePixmap:
        def scaled(
            self,
            width: int,
            height: int,
            aspect_ratio_mode: object,
            transformation_mode: object,
        ):
            assert width == 500
            assert height == 500
            return self

    cached_pixmap: Any = FakePixmap()
    manager.art_cache = {url: cached_pixmap}

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("urlopen should not be called for cached artwork")

    monkeypatch.setattr(mod, "urlopen", fail_urlopen)

    manager.load_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
        album_label_stub,
    )

    assert manager.current_art_url == url
    assert manager.displayed_art_url == url
    assert album_label_stub.pixmap is cached_pixmap


def test_load_art_uses_database_cache(
    monkeypatch: pytest.MonkeyPatch,
    album_label_stub: Any,
    fake_pixmap_class: type[Any],
):
    """`load_art` should populate the in-memory cache from the database cache."""
    mod = artwork_mod
    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))
    url = "http://fake-url.test/album.jpg"
    manager.database.insert_artwork_data(url, b"cached_bytes")

    monkeypatch.setattr(mod, "QPixmap", fake_pixmap_class)

    manager.load_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
        album_label_stub,
    )

    assert manager.displayed_art_url == url
    assert url in manager.art_cache
    assert manager.database.get_artwork_data(url) == b"cached_bytes"
    assert album_label_stub.pixmap is manager.art_cache[url]


def test_load_art_downloads_and_caches_artwork(
    monkeypatch: pytest.MonkeyPatch,
    album_label_stub: Any,
    fake_pixmap_class: type[Any],
    fake_image_factory: Any,
):
    """`load_art` should fetch, resize, cache, and persist downloaded artwork."""
    mod = artwork_mod
    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))
    url = "http://fake-url.test/album.jpg"

    class FakeResp:
        def __enter__(self) -> "FakeResp":
            return self

        def __exit__(self, *args: object, **kwargs: object) -> Literal[False]:
            return False

        def read(self):
            return b"downloaded_image_data"

    def fake_urlopen(
        _req: Any,
        *args: object,
        timeout: int = 3,
        **kwargs: object,
    ) -> FakeResp:
        return FakeResp()

    def fake_image_open(_data: Any) -> Any:
        return make_fake_image()

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    make_fake_image, _ = fake_image_factory
    monkeypatch.setattr(mod.Image, "open", fake_image_open)
    monkeypatch.setattr(mod, "QPixmap", fake_pixmap_class)

    manager.load_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
        album_label_stub,
    )

    cached = cast(Any, manager.art_cache[url])

    assert manager.current_art_url == url
    assert manager.displayed_art_url == url
    assert url in manager.art_cache
    assert cached.data == b"png-bytes"
    assert album_label_stub.pixmap is manager.art_cache[url]


def test_load_art_skips_already_displayed_artwork(monkeypatch: pytest.MonkeyPatch):
    """Test that `load_art` skips processing when the artwork URL is already displayed.
    This test creates a minimal `SonosApp`-like object with `current` set,
    and verifies that the method returns early when the artwork URL matches the displayed one.
    """
    mod = artwork_mod
    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))
    url = "http://fake-url.test/album.jpg"
    manager.displayed_art_url = url

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("urlopen should not be called for displayed artwork")

    monkeypatch.setattr(mod, "urlopen", fail_urlopen)

    # Create a minimal album label stub for testing
    class AlbumLabel:
        """Minimal album label stub for testing."""

        def __init__(self) -> None:
            self.pixmap: Any | None = None
            self.set_pixmap_calls = 0

        def setPixmap(self, pixmap: Any) -> None:
            self.pixmap = pixmap
            self.set_pixmap_calls += 1

    album_label = AlbumLabel()

    # Call load_art with the same URL as displayed_art_url
    manager.load_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
        cast(Any, album_label),
    )

    assert manager.current_art_url == url
    assert manager.displayed_art_url == url
    assert album_label.set_pixmap_calls == 0


def test_load_art_evicts_oldest_cached_artwork(
    monkeypatch: pytest.MonkeyPatch,
    album_label_stub: Any,
    fake_pixmap_class: type[Any],
    fake_image_factory: Any,
):
    """`load_art` should keep the in-memory artwork cache bounded."""
    mod = artwork_mod
    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))
    manager.art_cache = {
        f"http://fake-url.test/old-{index}.jpg": cast(Any, object())
        for index in range(manager.MAX_CACHE)
    }
    url = "http://fake-url.test/new.jpg"

    class FakeResp:
        def __enter__(self) -> "FakeResp":
            return self

        def __exit__(self, *args: object, **kwargs: object) -> Literal[False]:
            return False

        def read(self):
            return b"downloaded_image_data"

    def fake_urlopen(
        _req: Any, *args: object, timeout: int = 3, **kwargs: object
    ) -> FakeResp:
        return FakeResp()

    def fake_image_open(_data: Any) -> Any:
        return make_fake_image()

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    make_fake_image, _ = fake_image_factory
    monkeypatch.setattr(mod.Image, "open", fake_image_open)
    monkeypatch.setattr(mod, "QPixmap", fake_pixmap_class)

    manager.load_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
        album_label_stub,
    )

    assert len(manager.art_cache) == manager.MAX_CACHE
    assert "http://fake-url.test/old-0.jpg" not in manager.art_cache
    assert url in manager.art_cache
