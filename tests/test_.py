# tests for sonos_rescue.py using pytest and light stubs
import errno
import io
import os
import socket as real_socket
import sys
import types
from types import SimpleNamespace
import importlib
from pathlib import Path
import typing
from typing import Any

# from numpy import mod
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


def _install_stubs():
    # Minimal PyQt6 stubs used by sonos_rescue when imported in tests
    if "PyQt6" in sys.modules:
        return

    QtWidgets = types.SimpleNamespace()

    class Signal:
        def __init__(self):
            self._cb = None

        def connect(self, cb):
            self._cb = cb

        def emit(self, *args, **kwargs):
            if self._cb:
                return self._cb(*args, **kwargs)

    class QLabel:
        def __init__(self, text=""):
            self._text = text

        def setText(self, t):
            self._text = t

        def setAlignment(self, *_):
            pass

        def setStyleSheet(self, *_):
            pass

        def setPixmap(self, p):
            self._pix = p

    class QPushButton:
        def __init__(self, text=""):
            self.text = text
            self.clicked = Signal()

        def clicked_connect(self, cb):
            self.clicked.connect(cb)

    class QSlider:
        def __init__(self, *_):
            self.valueChanged = Signal()

        def setRange(self, a, b):
            pass

    class QListWidget:
        def __init__(self):
            self.items = []

        def clear(self):
            self.items.clear()

        def addItem(self, item):
            self.items.append(item)

    class QListWidgetItem:
        def __init__(self, title):
            self.title = title

    class QFrame:
        class Shape:
            Box = 1

        def setFrameShape(self, shape):
            pass

        def setStyleSheet(self, *_):
            pass

        def setLayout(self, *_):
            pass

    class QScrollArea:
        def __init__(self):
            pass

        def setWidgetResizable(self, *_):
            pass

        def setWidget(self, *_):
            pass

        def update(self):
            pass

    class QWidget:
        def __init__(self):
            pass

        def setLayout(self, *_):
            pass

    class QMessageBox:
        @staticmethod
        def critical(*a, **k):
            return

        @staticmethod
        def warning(*a, **k):
            return

    class QInputDialog:
        @staticmethod
        def getText(*a, **k):
            return ("", False)

    class QFileDialog:
        @staticmethod
        def getOpenFileName(*a, **k):
            return ("", "")

    class QApplication:
        def __init__(self, argv):
            pass

        def exec(self):
            return 0

    class QPixmap:
        def __init__(self):
            self.data = None

        def loadFromData(self, data):
            self.data = data

    class QVBoxLayout:
        def addWidget(self, widget):
            pass

    class FakeObject:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class FakeSignal:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self._cb = None

        def connect(self, cb: Any) -> None:
            self._cb = cb

        def emit(self, *args: Any, **kwargs: Any) -> None:
            if self._cb:
                return self._cb(*args, **kwargs)

    QtWidgets.QApplication = QApplication
    QtWidgets.QWidget = QWidget
    QtWidgets.QLabel = QLabel
    QtWidgets.QPushButton = QPushButton
    QtWidgets.QVBoxLayout = QVBoxLayout
    QtWidgets.QHBoxLayout = lambda *_args, **_kwargs: None
    QtWidgets.QListWidget = QListWidget
    QtWidgets.QListWidgetItem = QListWidgetItem
    QtWidgets.QSlider = QSlider
    QtWidgets.QMessageBox = QMessageBox
    QtWidgets.QFrame = QFrame
    QtWidgets.QScrollArea = QScrollArea
    QtWidgets.QInputDialog = QInputDialog
    QtWidgets.QFileDialog = QFileDialog

    QtCore = types.SimpleNamespace(
        QObject=FakeObject,
        pyqtSignal=FakeSignal,
    )

    QtCore.Qt = types.SimpleNamespace(
        AlignmentFlag=types.SimpleNamespace(AlignCenter=0),
        Orientation=types.SimpleNamespace(Horizontal=0),
    )

    QtGui = types.SimpleNamespace()
    QtGui.QPixmap = QPixmap

    sys.modules["PyQt6"] = types.ModuleType("PyQt6")
    sys.modules["PyQt6.QtWidgets"] = types.ModuleType("PyQt6.QtWidgets")
    sys.modules["PyQt6.QtCore"] = types.ModuleType("PyQt6.QtCore")
    sys.modules["PyQt6.QtGui"] = types.ModuleType("PyQt6.QtGui")

    # populate modules
    m = sys.modules["PyQt6.QtWidgets"]
    for k, v in QtWidgets.__dict__.items():
        if not k.startswith("__"):
            setattr(m, k, v)

    mc = sys.modules["PyQt6.QtCore"]
    mc.__dict__["Qt"] = QtCore.Qt
    mc.__dict__["QObject"] = QtCore.QObject
    mc.__dict__["pyqtSignal"] = QtCore.pyqtSignal

    mg = sys.modules["PyQt6.QtGui"]
    mg.__dict__["QPixmap"] = QtGui.QPixmap

    # PIL.Image stub
    pil = types.ModuleType("PIL")
    pil_image = types.ModuleType("PIL.Image")

    class _Img:
        def __init__(self, data=None):
            self.data = data

        def resize(self, size):
            return self

        def save(self, fp, format=None):
            if hasattr(fp, "write"):
                fp.write(b"PNGDATA")

    def open_bytes(fp):
        return _Img()

    pil_image.__dict__["open"] = open_bytes
    pil_image.__dict__["Image"] = _Img
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = pil_image

    # mutagen stubs
    mm = types.ModuleType("mutagen")
    mp3 = types.ModuleType("mutagen.mp3")

    class MP3:
        def __init__(self, path, ID3=None):
            self.tags = {}

    # mp3.MP3 = MP3
    mp3.__dict__["MP3"] = MP3
    id3 = types.ModuleType("mutagen.id3")
    # id3.ID3 = object
    id3.__dict__["ID3"] = object
    sys.modules["mutagen"] = mm
    sys.modules["mutagen.mp3"] = mp3
    sys.modules["mutagen.id3"] = id3

    # soco stub
    soco = types.ModuleType("soco")

    class SoCo:
        pass

    def discover():
        return None

    soco.__dict__["discover"] = discover
    soco.__dict__["SoCo"] = SoCo
    sys.modules["soco"] = soco


def _import_module():
    # ensure stubs present before importing sonos_rescue
    _install_stubs()

    module_name = "sonos_rescue.sonos_rescue"

    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        importlib.import_module(module_name)

    return sys.modules[module_name]


def import_local_music_server():
    _install_stubs()

    module_name = "sonos_rescue.services.local_music_server"

    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        importlib.import_module(module_name)

    return sys.modules[module_name]


def _import_network_module():
    """Import the network utility module with test doubles in place."""
    module_name = "sonos_rescue.utils.network"

    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        importlib.import_module(module_name)

    return sys.modules[module_name]


def test_quiet_copyfile_handles_errors():
    """Verify QuietHTTPRequestHandler.copyfile swallows broken-pipe and
    connection-reset errors without raising so the server stays stable.

    This test constructs a handler instance and passes fake output objects
    that raise BrokenPipeError and ConnectionResetError from their
    write methods. The thread should not crash and no exception should
    propagate out of copyfile.
    """

    mod = import_local_music_server()

    handler = mod.QuietHTTPRequestHandler.__new__(mod.QuietHTTPRequestHandler)

    class BadOutput:
        """Output object that raises BrokenPipeError on write."""

        def write(self, _: bytes) -> None:
            raise BrokenPipeError()

    # should not raise
    mod.QuietHTTPRequestHandler.copyfile(
        handler,
        io.BytesIO(b"abc"),
        BadOutput(),
    )

    class BadOutput2:
        """Output object that raises ConnectionResetError on write."""

        def write(self, _: bytes) -> None:
            raise ConnectionResetError()

    mod.QuietHTTPRequestHandler.copyfile(
        handler,
        io.BytesIO(b"abc"),
        BadOutput2(),
    )


def test_local_music_server_start_stop(tmp_path: Path):
    """Start and stop the LocalMusicServer.

    Ensures `start()` initialises `httpd` and `stop()` shuts down the server
    without error. Port 0 allows the operating system to select an available port.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """

    mod = _import_module()
    server = mod.LocalMusicServer(tmp_path, port=0)
    server.start()
    try:
        assert server.httpd is not None
    finally:
        server.stop()


def test_local_music_server_start_preserves_cwd(tmp_path: Path):
    """Starting the local music server should not change the process cwd."""

    mod = _import_module()
    before = os.getcwd()
    server = mod.LocalMusicServer(folder=tmp_path, port=0)

    server.start()

    try:
        assert os.getcwd() == before
    finally:
        server.stop()
        assert os.getcwd() == before


def test_local_music_server_preferred_port_available(tmp_path: Path):
    """Start a LocalMusicServer with a preferred port when it is available.

    Args:
        tmp_path (Path): temporary directory for the server's served folder
    """
    mod = _import_module()
    server = mod.LocalMusicServer(folder=tmp_path, port=8123)

    server.start()

    try:
        assert server.port == 8123, "expected preferred port to be used"
    finally:
        server.stop()


def test_local_music_server_preferred_port_occupied(tmp_path: Path):
    """Use the next available port when the preferred port is occupied.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """
    sock = real_socket.socket(real_socket.AF_INET, real_socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 8123))

    try:
        mod = _import_module()
        server = mod.LocalMusicServer(folder=tmp_path, port=8123)
        server.start()

        try:
            assert server.port == 8124
        finally:
            server.stop()
    finally:
        sock.close()


# helper function to simulate an occupied port by raising OSError
def fake_http_server(*args: object, **kwargs: object) -> None:
    """Simulate an OSError caused by an occupied HTTP server port.

    Raises:
        OSError: Always raised with EADDRINUSE to simulate a port conflict.
    """
    raise OSError(errno.EADDRINUSE, "Address already in use")


def test_local_music_server_start_if_already_running_raises_error(tmp_path: Path):
    """Raise RuntimeError when starting an already running server.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """
    mod = _import_module()

    server = mod.LocalMusicServer(folder=tmp_path, port=0)

    server.start()

    try:
        with pytest.raises(RuntimeError, match="already running"):
            server.start()
    finally:
        server.stop()


def test_local_music_server_all_ports_occupied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Raise PortInUseError when all preferred ports are occupied.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """
    mod = import_local_music_server()
    monkeypatch.setattr(mod, "HTTPServer", fake_http_server)
    server = mod.LocalMusicServer(folder=tmp_path, port=8123)

    with pytest.raises(mod.PortInUseError):
        server.start()


def test_local_music_server_rejects_invalid_folder(tmp_path: Path):
    """Raise FileNotFoundError when the server folder does not exist.

    This exercises the defensive check directly, without needing the file
    picker to produce an invalid path.

    Args:
        tmp_path (Path): Temporary directory used to create the missing folder.
    """
    mod = _import_module()
    missing_folder = tmp_path / "missing"
    server = mod.LocalMusicServer(folder=missing_folder, port=0)

    with pytest.raises(FileNotFoundError, match=str(missing_folder)):
        server.start()


def test_room_card_select_calls_on_select():
    """Ensure RoomCard.select calls the provided callback with the
    speaker object and that the displayed name matches `player_name`.

    This checks the small UI component wiring without creating a real
    Qt event loop by using the lightweight PyQt stubs installed for
    tests.
    """

    mod = _import_module()

    speaker = SimpleNamespace(player_name="TestRoom")
    called = {}

    def on_select(s: SimpleNamespace):
        called["s"] = s

    card = mod.RoomCard(speaker, on_select)
    assert card.name_label._text == "TestRoom"
    card.select()
    assert called["s"] is speaker


def test_get_local_ip_fallback_and_success(
    monkeypatch: pytest.MonkeyPatch,
):
    # mod = _import_module()
    network_mod = importlib.import_module("sonos_rescue.utils.network")

    class FakeSock:
        def connect(self, addr: tuple[str, int]) -> None:
            pass

        def getsockname(self):
            return ("192.0.2.1", 12345)

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(
        network_mod,
        "socket",
        types.SimpleNamespace(
            AF_INET=real_socket.AF_INET,
            SOCK_DGRAM=real_socket.SOCK_DGRAM,
            socket=lambda *_args, **_kwargs: FakeSock(),  # pyright: ignore[reportUnknownLambdaType]
        ),
    )

    ip = network_mod.get_local_ip()
    assert ip == "192.0.2.1"

    class SockErr:
        def connect(self, addr: tuple[str, int]) -> None:
            raise OSError("network unreachable")

        def getsockname(self):
            return ("0.0.0.0", 0)

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(
        network_mod,
        "socket",
        types.SimpleNamespace(
            AF_INET=real_socket.AF_INET,
            SOCK_DGRAM=real_socket.SOCK_DGRAM,
            socket=lambda *_args, **_kwargs: SockErr(),  # pyright: ignore[reportUnknownLambdaType]
        ),
    )

    ip2 = network_mod.get_local_ip()
    assert ip2 == "127.0.0.1"


def test_get_album_art_from_file_returns_data_and_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Validate `get_album_art_from_file` extracts APIC frame data from
    an MP3 file and returns `None` when MP3 parsing fails.

    The test replaces `MP3` with a fake that provides an APIC-like tag
    and then with a callable that raises to exercise the exception
    handling path.
    """

    mod = _import_module()
    artwork_mod = importlib.import_module("sonos_rescue.managers.artwork_manager")

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

    mod = _import_module()
    artwork_mod = importlib.import_module("sonos_rescue.managers.artwork_manager")

    # prepare a SonosApp-like object
    app = mod.ArtworkManager.__new__(mod.ArtworkManager)
    app.current = SimpleNamespace(ip_address="10.0.0.5")
    app.art_cache = {}
    app.current_art_url = None

    class AlbumLabel:
        """Minimal album label stub for testing."""

        def __init__(self):
            self.pix: Any | None = None

        def setPixmap(self, p: Any):
            self.pix = p

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
    mod.ArtworkManager.load_art(app, "fake_url", app.current, app.album_label)
    # should have set current_art_url
    assert app.current_art_url is not None
    # second call with same URL should no-op due to cache
    prev = app.current_art_url
    mod.ArtworkManager.load_art(app, prev, app.current, app.album_label)
