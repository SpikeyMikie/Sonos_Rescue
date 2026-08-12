# tests for sonos_rescue.py using pytest and light stubs
import socket as real_socket
import sys
import types
from types import SimpleNamespace
import importlib
from pathlib import Path
from typing import Any
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


# helper function to simulate an occupied port by raising OSError


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
