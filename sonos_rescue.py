"""
Main entry point for the Sonos Rescue application.

Creates the PyQt6 application instance, initialises the main window,
and starts the event loop.
"""

# Standard library
import os
import socket
import shutil
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Callable, Protocol, cast
from urllib.request import Request, urlopen

# Third-party libraries
import soco  # type: ignore[reportMissingTypeStubs]
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from PIL import Image
from PIL.Image import Image as PILImage

# GUI framework
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# Type checking exceptions
from soco import SoCo  # type: ignore[reportMissingTypeStubs]


# custom class for tbc
class QueueItemProtocol(Protocol):
    """
    Defines the minimum interface required for Sonos queue items.

    SoCo queue objects contain many attributes, but this application
    only requires the track title for displaying the queue.
    """

    title: str


# custom class for tbc
class APICProtocol(Protocol):
    """
    Defines the attributes required from Mutagen album artwork frames.

    Used to extract embedded cover art from MP3 files while avoiding
    dependency on Mutagen's incomplete type information.
    """

    FrameID: str
    type: int
    data: bytes


# custom handler to suppress logging and handle broken connections gracefully
class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for serving local music files to Sonos devices.

    Extends Python's built-in SimpleHTTPRequestHandler to:
    - Prevent server crashes when Sonos disconnects unexpectedly.
    - Suppress default HTTP request logging to keep the console output clean.

    This handler is used by the local HTTP server to make locally stored
    music files accessible through HTTP URLs that Sonos can play.
    """

    def copyfile(  # type: ignore[override]
        self, source: BinaryIO, outputfile: BinaryIO
    ) -> None:
        """
        Copy file data from the requested resource to the HTTP response.

        Overrides the parent class method to gracefully handle cases where
        the Sonos device disconnects before the file transfer completes.

        Args:
            source:
                The file object containing the requested file data.
            outputfile:
                The file object used to send data back to the client.

        Returns:
            None
        """

        try:
            shutil.copyfileobj(source, outputfile)

        # Sonos may stop requesting data before the transfer finishes,
        # causing the client connection to close unexpectedly.
        except (BrokenPipeError, ConnectionResetError):
            pass

    # suppress logging
    def log_message(self, format: str, *args: object) -> None:
        """
        Disable default HTTP server request logging.

        The parent SimpleHTTPRequestHandler logs every request to the
        terminal. This is unnecessary for normal operation and would
        clutter the application's output.
        """


class LocalMusicServer:
    """
    A lightweight HTTP server for serving local music files to Sonos devices.

    Sonos speakers cannot play files directly from the local filesystem, instead
    they require media to be accessible via an HTTP URL.

    The server runs in a daemon thread, allowing it to operate alongside the
    main application without blocking the GUI.
    """

    def __init__(self, folder: Path, port: int = 8000) -> None:
        """
        Initialise the local music server.

        Args:
        folder:
            Directory containing the music files to serve.
        port (optional):
            TCP port on which the HTTP server listens.
            Defaults to 8000.
        """
        self.folder: Path = folder
        self.port: int = port
        self.httpd: HTTPServer | None = None

    def start(self) -> None:
        """
        Start the HTTP server in a background thread.

        The server changes the working directory to the configured music
        folder before serving files. Running the server in a daemon thread
        allows the GUI to remain responsive while music is streamed to
        Sonos devices.
        """

        # Serve files relative to the selected music directory.
        os.chdir(self.folder)

        handler = QuietHTTPRequestHandler
        self.httpd = HTTPServer(("0.0.0.0", self.port), handler)

        # Run the HTTP server in the background so it does not block the GUI.
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()

    def stop(self) -> None:
        """
        Stop the HTTP server if it is running.

        Shuts down the background server, preventing any new HTTP requests
        from being accepted.
        """
        if self.httpd:
            self.httpd.shutdown()


class RoomCard(QFrame):
    """
    A GUI card representing a Sonos speaker.

    Displays basic information about a discovered speaker and provides a
    button that allows the user to select it for control. Multiple
    RoomCard widgets can be displayed together to create a list of
    available Sonos devices on the network.
    """

    def __init__(self, speaker: SoCo, on_select: Callable[[SoCo], None]) -> None:
        """
        Initialise a room card for a Sonos speaker.

        Args:
            speaker:
                The SoCo speaker instance represented by this card.
            on_select:
                Callback function executed when the user selects the
                speaker for control.
        """
        super().__init__()
        self.speaker: SoCo = speaker
        self.on_select: Callable[[SoCo], None] = on_select

        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("padding:10px; margin:5px; border-radius:8px;")

        layout = QVBoxLayout()

        self.name_label = QLabel(speaker.player_name)
        self.status_label = QLabel("Idle")

        self.control_button = QPushButton("Control")
        self.control_button.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.select
        )

        layout.addWidget(self.name_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.control_button)

        self.setLayout(layout)

    def select(self) -> None:
        """
        Notify the parent application that this speaker has been selected.

        Invokes the callback (created in init), passing the
        associated instance.
        """
        self.on_select(self.speaker)


class SonosApp(QWidget):
    """
    This class builds the gui -
    - discovering Sonos speakers on the local network,
    - handling user interactions
    - coordinating playback control through the SoCo library.

    It also;
    - manages the local HTTP server used to stream local audio files
    - periodically updates the now playing information
    - caches album artwork.
    """

    def __init__(self):
        """
        Initialise the main application window.

        Sets up the application state, builds the user interface, discovers
        available Sonos speakers, and starts the background refresh thread
        used to keep the displayed playback information up to date.
        """
        super().__init__()
        self.setWindowTitle("Sonos Desktop Controller")
        self.setGeometry(100, 100, 1200, 700)

        # Sonos devices and playback state
        self.speakers: list[SoCo] = []
        self.current: SoCo | None = None

        # Album artwork cache
        self.art_cache: dict[str, QPixmap] = {}
        self.current_art_url: str | None = None

        # Local music server
        self.server: LocalMusicServer | None = None

        # Build the interface and discover speakers
        self.build_ui()
        self.discover_speakers()

        # Start background refresh thread
        self.running = True
        threading.Thread(target=self.refresh_loop, daemon=True).start()

    # ------------------------------------------------------------------
    # User interface construction
    # ------------------------------------------------------------------

    def build_ui(self) -> None:
        """
        Construct the main application interface.

        Creates the three-panel layout consisting of the speaker list,
        playback controls, and queue display, and connects the relevant
        UI controls to their event handlers.
        """
        root = QHBoxLayout()

        # Left panel: discovered Sonos speakers / rooms
        self.rooms_container_widget = QWidget()
        self.rooms_layout = QVBoxLayout(self.rooms_container_widget)

        self.rooms_label = QLabel("Rooms")
        self.rooms_layout.addWidget(self.rooms_label)

        self.rooms_scroll = QScrollArea()
        self.rooms_scroll.setWidgetResizable(True)
        self.rooms_scroll.setWidget(self.rooms_container_widget)

        # Center panel: now playing information and playback controls
        center_layout = QVBoxLayout()

        self.title = QLabel("No room selected")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:18px;")

        self.album = QLabel()
        self.album.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.track_info = QLabel("")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_layout.addWidget(self.title)
        center_layout.addWidget(self.album)
        center_layout.addWidget(self.track_info)

        controls = QHBoxLayout()

        self.play_btn = QPushButton("Play/Pause")

        self.play_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.play_pause
        )

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.next_track
        )

        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.prev_track
        )

        controls.addWidget(self.play_btn)
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.next_btn)

        center_layout.addLayout(controls)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.valueChanged.connect(  # pyright: ignore[reportUnknownMemberType]
            self.set_volume
        )

        center_layout.addWidget(QLabel("Volume"))
        center_layout.addWidget(self.volume)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # Right panel: playback queue and utility actions
        right_layout = QVBoxLayout()

        self.queue = QListWidget()

        self.refresh_btn = QPushButton("Refresh Rooms")
        self.refresh_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.discover_speakers
        )

        right_layout.addWidget(QLabel("Queue"))
        right_layout.addWidget(self.queue)

        self.add_file_btn = QPushButton("Play Local File")
        self.add_file_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.play_local_file
        )
        right_layout.addWidget(self.add_file_btn)

        self.add_uri_btn = QPushButton("Add URL / URI to Queue")
        self.add_uri_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.add_to_queue
        )
        right_layout.addWidget(self.add_uri_btn)
        right_layout.addWidget(self.refresh_btn)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Assemble
        root.addWidget(self.rooms_scroll, 2)
        root.addWidget(center_widget, 3)
        root.addWidget(right_widget, 2)

        self.setLayout(root)

    # ------------------------------------------------------------------
    # Speaker discovery
    # ------------------------------------------------------------------

    # Discover available Sonos speakers
    def discover_speakers(self) -> None:
        """
        Discover Sonos speakers on the local network.

        Clears any existing room cards and rebuilds the speaker list to
        reflect the currently available devices.
        """
        try:
            devices = cast(
                set[SoCo] | None,
                soco.discover(),  # pyright: ignore[reportUnknownMemberType]
            )
            self.speakers = list(devices) if devices else []

            # clear old cards
            for i in reversed(range(self.rooms_layout.count())):
                item = self.rooms_layout.itemAt(i)
                widget = item.widget() if item else None
                if widget:
                    widget.setParent(None)
            # add new cards
            for s in self.speakers:
                card = RoomCard(s, self.select_speaker)
                self.rooms_layout.addWidget(card)

            # adjust scroll area
            self.rooms_container_widget.adjustSize()
            self.rooms_scroll.update()
            self.rooms_container_widget.update()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def select_speaker(self, speaker: SoCo) -> None:
        """
        Make the selected speaker the active playback device.

        Args:
            speaker: The SoCo speaker instance selected by the user.
        """
        self.current = speaker
        self.title.setText(speaker.player_name)

    # ------------------------------------------------------------------
    # Playback controls
    # ------------------------------------------------------------------

    def play_pause(self) -> None:
        """Toggle playback for the selected speaker."""
        if not self.current:
            return

        try:
            state = self.current.get_current_transport_info()["current_transport_state"]

            if state == "PLAYING":
                self.current.pause()
                self.play_btn.setText("Pause")
            else:
                self.current.play()  # pyright: ignore[reportUnknownMemberType]
                self.play_btn.setText("Play")

        except Exception as e:
            print("Play/Pause error:", e)

    def next_track(self) -> None:
        """Skip to the next track."""
        if self.current:
            self.current.next()

    def prev_track(self) -> None:
        """Return to the previous track."""
        if self.current:
            self.current.previous()

    def set_volume(self, v: int) -> None:
        """Set the volume of the selected speaker."""
        if self.current:
            self.current.volume = v

    # ------------------------------------------------------------------
    # Now playing info
    # ------------------------------------------------------------------

    def update_now_playing(self) -> None:
        """
        Update the playback information displayed in the GUI -
        - Retrieves the currently playing track
        - refreshes the playback queue
        - updates the displayed album artwork when it changes.
        """
        if not self.current:
            return

        try:
            track = self.current.get_current_track_info()
            title = track.get("title", "")
            artist = track.get("artist", "")
            album = track.get("album", "")
            self.track_info.setText(f"{title}\n{artist}\n{album}")
            art: str | None = track.get("album_art")

            if art != self.current_art_url:  # reset cache if art URL changes
                if self.current_art_url is not None:
                    self.art_cache.pop(self.current_art_url, None)  # remove old cache
                self.current_art_url = art  # reset current art URL

            if art:
                self.load_art(art)

            # update queue (lightweight)
            q = cast(list[QueueItemProtocol], self.current.get_queue())
            self.queue.clear()

            for item in q:
                self.queue.addItem(item.title)
        except Exception:
            pass

    def play_local_file(self) -> None:
        """
        Play a local audio file through the selected Sonos speaker.

        Starts the local HTTP server if required, extracts embedded album
        artwork from the audio file, and instructs the speaker to stream the
        file using its generated HTTP URL.
        """
        if not self.current:
            return

        # moved import here to avoid unnecessary dependency if not using this feature
        from PyQt6.QtWidgets import QFileDialog

        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Music File", "", "Audio Files (*.mp3 *.wav *.m4a)"
        )

        # CRITICAL: stop immediately if no file selected
        if not file_path_str:
            return

        file_path = Path(file_path_str)

        try:
            filename = file_path.name

            # Extract album art FIRST (safe now)
            art_data = self.get_album_art_from_file(file_path)
            if art_data:
                pixmap = QPixmap()
                pixmap.loadFromData(art_data)
                self.album.setPixmap(pixmap)

            # Sonos cannot access local filesystem paths directly.
            # A temporary HTTP server exposes the selected file so the speaker
            # can stream it using a normal URL.
            if self.server is None:
                self.server = LocalMusicServer(file_path.parent, 8000)
                self.server.start()
            else:
                self.server.folder = file_path.parent
                os.chdir(str(self.server.folder))

            # Build URL
            from urllib.parse import quote

            ip = self.get_local_ip()
            url = f"http://{ip}:8000/{quote(filename)}"

            print("Playing:", url)

            # Play on Sonos
            self.current.play_uri(url)  # pyright: ignore[reportUnknownMemberType]

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def get_album_art_from_file(self, file_path: str | Path) -> bytes | None:
        """
        Extract any embedded front-cover artwork from an MP3 file.

        Returns:
            bytes | None: The embedded image data, or None if no artwork is
            available.
        """
        file_path = Path(file_path)

        try:
            audio = MP3(file_path, ID3=ID3)

            tags = cast(dict[object, APICProtocol] | None, audio.tags)  # type: ignore

            if tags is None:
                return None

            for tag in tags.values():
                if getattr(tag, "FrameID", None) == "APIC":
                    if getattr(tag, "type", None) == 3:  # 3 = front cover
                        return tag.data

        except Exception as e:
            print("Album art error:", e)

        return None

    def get_local_ip(self) -> str:
        """
        Determine the local IPv4 address of this machine.

        A UDP socket is used only to discover the preferred network interface.
        No data is actually sent to the remote address (google).
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    # Load and display album art from URL
    def load_art(self, url: str) -> None:
        """
        Download and display album artwork.

        Album artwork is cached in memory to reduce network requests and
        improve UI responsiveness when the same artwork is displayed again.
        """
        speaker = self.current
        if not speaker:
            return

        try:
            if not url.startswith("http"):
                speaker_ip = cast(str, speaker.ip_address)  # type: ignore
                url = f"http://{speaker_ip}:1400{url}"

            # If same URL as last time do nothing
            if url == self.current_art_url:
                return

            self.current_art_url = url

            # If cached use it
            if url in self.art_cache:
                self.album.setPixmap(self.art_cache[url])
                return

            # Otherwise fetch it
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=3) as response:
                image_bytes = response.read()

            image_file: PILImage = Image.open(BytesIO(image_bytes))
            size: tuple[int, int] = (300, 300)
            resized_image = resize_image(image_file, size)

            png_buffer = BytesIO()
            resized_image.save(png_buffer, format="PNG")

            pixmap = QPixmap()
            pixmap.loadFromData(png_buffer.getvalue())

            # Store in cache
            self.art_cache[url] = pixmap
            MAX_CACHE = 20

            if len(self.art_cache) > MAX_CACHE:
                self.art_cache.pop(next(iter(self.art_cache)))

            self.album.setPixmap(pixmap)

        except Exception as e:
            print("Album load error:", e)

    # ------------------------------------------------------------------
    # Background refresh
    # ------------------------------------------------------------------

    def refresh_loop(self) -> None:
        """
        Background worker that refreshes playback information (every 2 secs).

        Runs in a daemon thread, for the lifetime of the application.
        """
        while self.running:
            try:
                self.update_now_playing()
            except:
                pass
            time.sleep(2)

    def add_to_queue(self) -> None:
        """
        Add a network stream or Sonos-compatible URI to the playback queue.

        Prompts the user for a URI and updates the displayed queue after the
        item has been added.
        """
        if not self.current:
            QMessageBox.warning(self, "No speaker", "Select a room first")
            return

        url, ok = QInputDialog.getText(
            self, "Add URL / URI to Queue", "Enter stream URL or Sonos-supported URI:"
        )

        if not ok or not url:
            return

        try:
            # OPTION 1: add to queue
            self.current.add_to_queue(url)  # pyright: ignore[reportUnknownMemberType]

            # refresh queue view immediately
            self.update_now_playing()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


def resize_image(image: PILImage, size: tuple[int, int]) -> PILImage:
    """
    Resize a Pillow image to the requested dimensions.

    Kept separate from the main album-loading function to isolate
    image manipulation logic.
    """
    return image.resize(size)  # pyright: ignore[reportUnknownMemberType]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SonosApp()
    window.show()
    sys.exit(app.exec())
