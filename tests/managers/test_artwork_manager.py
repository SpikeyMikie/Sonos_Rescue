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


def test_resolve_and_fetch_art_uses_database_cache(monkeypatch: pytest.MonkeyPatch):
    """A database hit returns bytes without constructing Qt objects."""
    mod = artwork_mod
    manager = mod.ArtworkManager(ArtworkDatabase(":memory:"))
    url = "http://fake-url.test/album.jpg"
    manager.database.insert_artwork_data(url, b"cached_bytes")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("urlopen should not be called for database cache hits")

    monkeypatch.setattr(mod, "urlopen", fail_urlopen)

    result = manager.resolve_and_fetch_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
    )

    assert result.art_url == url
    assert result.art_bytes == b"cached_bytes"
    assert result.is_new is False


def test_resolve_and_fetch_art_downloads_and_persists_artwork(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_factory: Any,
):
    """A cache miss fetches, resizes, encodes, and persists PNG bytes."""
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

    result = manager.resolve_and_fetch_art(
        url,
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
    )

    assert result.art_url == url
    assert result.art_bytes == b"png-bytes"
    assert result.is_new is True
    assert manager.database.get_artwork_data(url) == b"png-bytes"


def test_resolve_and_fetch_art_rejects_invalid_url():
    """Invalid artwork URLs produce an empty result without side effects."""
    manager = artwork_mod.ArtworkManager(ArtworkDatabase(":memory:"))

    result = manager.resolve_and_fetch_art(
        "http://fake-url.test/album.txt",
        cast(Any, SimpleNamespace(ip_address="10.0.0.5")),
    )

    assert result.art_url is None
    assert result.art_bytes is None
    assert result.is_new is False
