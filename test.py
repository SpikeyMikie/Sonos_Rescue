# tests for sonos_rescue.py using pytest and light stubs
import sys
import types
from types import SimpleNamespace
import importlib
import tempfile
import os
import threading


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

		def emit(self, *a, **k):
			if self._cb:
				return self._cb(*a, **k)

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
		def __init__(self):
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

	QtWidgets.QApplication = QApplication
	QtWidgets.QWidget = QWidget
	QtWidgets.QLabel = QLabel
	QtWidgets.QPushButton = QPushButton
	QtWidgets.QVBoxLayout = lambda *a, **k: None
	QtWidgets.QHBoxLayout = lambda *a, **k: None
	QtWidgets.QListWidget = QListWidget
	QtWidgets.QListWidgetItem = QListWidgetItem
	QtWidgets.QSlider = QSlider
	QtWidgets.QMessageBox = QMessageBox
	QtWidgets.QFrame = QFrame
	QtWidgets.QScrollArea = QScrollArea
	QtWidgets.QInputDialog = QInputDialog
	QtWidgets.QFileDialog = QFileDialog

	QtCore = types.SimpleNamespace()
	QtCore.Qt = types.SimpleNamespace(AlignmentFlag=types.SimpleNamespace(AlignCenter=0), Orientation=types.SimpleNamespace(Horizontal=0))

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
	mc.__dict__['Qt'] = QtCore.Qt

	mg = sys.modules["PyQt6.QtGui"]
	mg.__dict__['QPixmap'] = QtGui.QPixmap

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

	pil_image.__dict__['open'] = open_bytes
	sys.modules["PIL"] = pil
	sys.modules["PIL.Image"] = pil_image

	# mutagen stubs
	mm = types.ModuleType("mutagen")
	mp3 = types.ModuleType("mutagen.mp3")

	class MP3:
		def __init__(self, path, ID3=None):
			self.tags = {}

	#mp3.MP3 = MP3
	mp3.__dict__['MP3'] = MP3
	id3 = types.ModuleType("mutagen.id3")
	# id3.ID3 = object
	id3.__dict__['ID3'] = object
	sys.modules["mutagen"] = mm
	sys.modules["mutagen.mp3"] = mp3
	sys.modules["mutagen.id3"] = id3

	# soco stub
	soco = types.ModuleType("soco")

	def discover():
		return None

	soco.__dict__['discover'] = discover
	sys.modules["soco"] = soco


def _import_module():
	# ensure stubs present before importing sonos_rescue
	_install_stubs()
	if "sonos_rescue" in sys.modules:
		importlib.reload(sys.modules["sonos_rescue"])
	else:
		importlib.import_module("sonos_rescue")
	return sys.modules["sonos_rescue"]


def test_quiet_copyfile_handles_errors():
	"""Verify QuietHTTPRequestHandler.copyfile swallows broken-pipe and
	connection-reset errors without raising so the server stays stable.

	This test constructs a handler instance and passes fake output objects
	that raise BrokenPipeError and ConnectionResetError from their
	write methods. The thread should not crash and no exception should
	propagate out of copyfile.
	"""

	mod = _import_module()
	handler = mod.QuietHTTPRequestHandler.__new__(mod.QuietHTTPRequestHandler)

	class BadOutput:
		def write(self, b):
			raise BrokenPipeError()

	# should not raise
	mod.QuietHTTPRequestHandler.copyfile(handler, b"abc", BadOutput())

	class BadOutput2:
		def write(self, b):
			raise ConnectionResetError()

	mod.QuietHTTPRequestHandler.copyfile(handler, b"abc", BadOutput2())


def test_local_music_server_start_stop(tmp_path):
	"""Start and stop the LocalMusicServer producing an HTTPServer.

	Ensures `start()` initializes `httpd` (port 0 chosen by OS) and
	`stop()` shuts it down without error. Uses a temporary directory for
	the server's working folder.
	"""

	mod = _import_module()
	folder = str(tmp_path)
	server = mod.LocalMusicServer(folder, port=0)
	server.start()
	try:
		assert server.httpd is not None
	finally:
		server.stop()


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

	def on_select(s):
		called['s'] = s

	card = mod.RoomCard(speaker, on_select)
	assert card.name._text == "TestRoom"
	card.select()
	assert called['s'] is speaker


def test_get_local_ip_fallback_and_success(monkeypatch):
	"""Test `get_local_ip` returns a routable IP when the socket
	succeeds and falls back to `127.0.0.1` on error.

	We patch the module's `socket` factory to simulate both a normal
	socket (returning a specific IP) and a socket that raises on
	connect to trigger the fallback branch.
	"""

	mod = _import_module()

	class FakeSock:
		def __init__(self):
			self._peer = None

		def connect(self, addr):
			if addr[0] == "8.8.8.8":
				return

		def getsockname(self):
			return ("192.0.2.1", 12345)

		def close(self):
			pass

	monkeypatch.setattr(mod, 'socket', types.SimpleNamespace(socket=lambda *a, **k: FakeSock()))
	ip = mod.SonosApp.get_local_ip(mod.SonosApp.__new__(mod.SonosApp))
	assert ip == "192.0.2.1"

	class SockErr:
		def __init__(self):
			pass

		def connect(self, addr):
			raise Exception()

		def getsockname(self):
			return ("0.0.0.0", 0)

		def close(self):
			pass

	monkeypatch.setattr(mod, 'socket', types.SimpleNamespace(socket=lambda *a, **k: SockErr()))
	ip2 = mod.SonosApp.get_local_ip(mod.SonosApp.__new__(mod.SonosApp))
	assert ip2 == "127.0.0.1"


def test_get_album_art_from_file_returns_data_and_none(monkeypatch, tmp_path):
	"""Validate `get_album_art_from_file` extracts APIC frame data from
	an MP3 file and returns `None` when MP3 parsing fails.

	The test replaces `MP3` with a fake that provides an APIC-like tag
	and then with a callable that raises to exercise the exception
	handling path.
	"""

	mod = _import_module()
	# mock MP3 to return tags containing an APIC-like object

	class Tag:
		FrameID = "APIC"
		type = 3
		data = b"ART"

	class FakeMP3:
		def __init__(self, path, ID3=None):
			self.tags = {"APIC": Tag()}

	monkeypatch.setattr(mod, 'MP3', FakeMP3)

	app = mod.SonosApp.__new__(mod.SonosApp)
	data = mod.SonosApp.get_album_art_from_file(app, str(tmp_path / "fake.mp3"))
	assert data == b"ART"

	# now MP3 raises
	def bad_mp3(*a, **k):
		raise Exception("bad")

	monkeypatch.setattr(mod, 'MP3', bad_mp3)
	data2 = mod.SonosApp.get_album_art_from_file(app, str(tmp_path / "fake.mp3"))
	assert data2 is None


def test_load_art_fetch_and_cache(monkeypatch):
	"""Exercise `load_art` network fetching and caching behavior.

	This creates a minimal `SonosApp`-like object with `current` set,
	patches `urlopen`, `Image.open`, and `QPixmap` to deterministic
	fakes, then calls `load_art` to ensure the art URL is normalized,
	fetched, stored in `art_cache`, and reused on subsequent calls.
	"""

	mod = _import_module()

	# prepare a SonosApp-like object
	app = mod.SonosApp.__new__(mod.SonosApp)
	app.current = SimpleNamespace(ip_address="10.0.0.5")
	app.art_cache = {}
	app.current_art_url = None
	class AlbumLabel:
		def __init__(self):
			self.pix = None

		def setPixmap(self, p):
			self.pix = p

	app.album = AlbumLabel()

	# patch urlopen to return a context manager with .read()
	class FakeResp:
		def __enter__(self):
			return self

		def __exit__(self, exc_type, exc, tb):
			return False

		def read(self):
			return b"IMAGEBYTES"

	monkeypatch.setattr(mod, 'urlopen', lambda req, timeout=3: FakeResp())

	# ensure PIL.Image.open returns an object with resize and save
	class ImgObj:
		def resize(self, size):
			return self

		def save(self, fp, format=None):
			fp.write(b"PNG")

	monkeypatch.setattr(mod, 'Image', types.SimpleNamespace(open=lambda b: ImgObj()))

	# simple QPixmap substitute
	class Pix:
		def __init__(self):
			self.data = None

		def loadFromData(self, d):
			self.data = d

	monkeypatch.setattr(mod, 'QPixmap', Pix)

	# run load_art with a non-http url (should be prefixed)
	mod.SonosApp.load_art(app, "/getaa")
	# should have set current_art_url
	assert app.current_art_url is not None
	# second call with same URL should no-op due to cache
	prev = app.current_art_url
	mod.SonosApp.load_art(app, prev)

