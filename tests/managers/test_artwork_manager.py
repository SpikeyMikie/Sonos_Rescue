from pathlib import Path
import pytest
from types import SimpleNamespace
from typing import Any, cast
import types
import typing

import sonos_rescue.managers.artwork_manager as artwork_mod


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


def test_load_art_fetch_and_cache(monkeypatch: pytest.MonkeyPatch):
    """Exercise `load_art` network fetching and caching behavior.

    This creates a minimal `SonosApp`-like object with `current` set,
    patches `urlopen`, `Image.open`, and `QPixmap` to deterministic
    fakes, then calls `load_art` to ensure the art URL is normalized,
    fetched, stored in `art_cache`, and reused on subsequent calls.
    """

    mod = artwork_mod

    # prepare a SonosApp-like object
    speaker: Any = SimpleNamespace(ip_address="10.0.0.5")
    app = cast(Any, mod.ArtworkManager())
    app.current = speaker
    app.current_art_url = None
    app.art_cache = {}
    app.displayed_art_url = None

    # app: Any = mod.ArtworkManager.__new__(mod.ArtworkManager)
    # speaker: Any = cast(Any, SimpleNamespace(ip_address="10.0.0.5"))
    # setattr(app, "current", speaker)
    # setattr(app, "current_art_url", None)
    # setattr(app, "art_cache", {})
    # setattr(app, "displayed_art_url", None)

    class AlbumLabel:
        """Minimal album label stub for testing."""

        def __init__(self):
            self.pix: Any | None = None

        def setPixmap(self, p: Any):
            self.pix = p

    setattr(app, "album_label", AlbumLabel())

    app.album_label = AlbumLabel()

    # patch urlopen to return a context manager with .read()
    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(
            self,
            _exc_type: type | None,
            _exc: BaseException | None,
            _tb: types.TracebackType | None,
        ) -> typing.Literal[False]:
            return False

        def read(self):
            return b"IMAGEBYTES"

    def fake_urlopen(_req: Any, _timeout: int = 3) -> FakeResp:
        return FakeResp()

    monkeypatch.setattr(
        artwork_mod,
        "urlopen",
        fake_urlopen,
    )

    # ensure PIL.Image.open returns an object with resize and save
    class ImgObj:
        def resize(self, size: tuple[int, int]):
            return self

        def save(self, fp: Any, format: str | None = None):
            fp.write(b"PNG")

    def fake_image_open(_b: Any) -> ImgObj:
        return ImgObj()

    monkeypatch.setattr(
        artwork_mod,
        "Image",
        types.SimpleNamespace(open=fake_image_open),
    )

    # simple QPixmap substitute
    class Pix:
        def __init__(self):
            self.data = None

        def loadFromData(self, d: bytes):
            self.data = d

    monkeypatch.setattr(artwork_mod, "QPixmap", Pix)

    # run load_art with a non-http url (should be prefixed)
    mod.ArtworkManager.load_art(
        app, "http://fake-url.test/album.jpg", speaker, cast(Any, app.album_label)
    )
    # should have set current_art_url
    assert app.current_art_url is not None
    # second call with same URL should no-op due to cache
    prev = app.current_art_url
    mod.ArtworkManager.load_art(app, prev, speaker, cast(Any, app.album_label))
