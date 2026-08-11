"""
Main entry point for the Sonos Rescue application.

Creates the PyQt6 application instance, initialises the main window,
and starts the event loop.
"""

# Standard library
import sys
import threading
import time
from pathlib import Path
from typing import (
    Protocol,
    cast,
)

# Type checking exceptions
from soco import SoCo  # type: ignore[import-untyped]

# GUI framework
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
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
    QFileDialog,
)

# internal app imports
from .services.local_music_server import LocalMusicServer
from .managers.speaker_manager import SpeakerManager
from .managers.playback_controller import PlaybackController
from .managers.artwork_manager import ArtworkManager
from .ui.room_card import RoomCard
from .utils.network import get_local_ip


class QueueItemProtocol(Protocol):
    """
    Defines the minimum interface required for Sonos queue items.

    SoCo queue objects contain many attributes, but this application
    only requires the track title for displaying the queue.
    """

    title: str


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

    def __init__(self) -> None:
        """
        Initialise the main application window.

        Sets up the application state, builds the user interface, discovers
        available Sonos speakers, and starts the background refresh thread
        used to keep the displayed playback information up to date.
        """
        super().__init__()
        self.port: int = LocalMusicServer.DEFAULT_PORT
        self.setWindowTitle("Sonos Desktop Controller")
        self.setGeometry(100, 100, 1200, 700)

        self.current: SoCo | None = None
        self.server: LocalMusicServer | None = None

        self.speaker_manager = SpeakerManager()
        self.artwork_manager: ArtworkManager = ArtworkManager()
        self.playback_controller = PlaybackController(
            get_current_speaker=lambda: self.current
        )

        self.play_btn: QPushButton
        self.build_ui()

        self.speaker_manager.speakers_discovered.connect(  # pyright: ignore[reportUnknownMemberType]
            self.display_speakers
        )
        self.speaker_manager.speaker_selected.connect(  # pyright: ignore[reportUnknownMemberType]
            self.display_selected_speaker
        )

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

        self.play_btn = QPushButton("Play/Pause")

        self.play_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.handle_play_pause
        )

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.playback_controller.next_track
        )

        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.playback_controller.prev_track
        )

        controls = QHBoxLayout()
        controls.addWidget(self.play_btn)
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.next_btn)

        center_layout.addLayout(controls)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.valueChanged.connect(  # pyright: ignore[reportUnknownMemberType]
            self.playback_controller.set_volume
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
            self.speaker_manager.discover_speakers
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
    # Display speakers and selected speaker
    # ------------------------------------------------------------------

    def display_speakers(self, speakers: list[SoCo]) -> None:
        """
        Update the GUI with the list of discovered Sonos speakers.

        Clears any existing room cards and rebuilds the speaker list to
        reflect the currently available devices.
        """
        self.speakers = speakers

        # clear old cards
        for i in reversed(range(self.rooms_layout.count())):
            item = self.rooms_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                widget.setParent(None)

        # add new cards
        for s in self.speakers:
            card = RoomCard(s, self.speaker_manager.select_speaker)
            self.rooms_layout.addWidget(card)

        # adjust scroll area
        self.rooms_container_widget.adjustSize()
        self.rooms_scroll.update()
        self.rooms_container_widget.update()

    def display_selected_speaker(self, speaker: SoCo) -> None:
        """
        Update the GUI to reflect the currently selected Sonos speaker.

        Displays the speaker's name and resets the now playing information.
        """
        self.current = speaker
        self.title.setText(speaker.player_name)
        self.track_info.setText("")
        self.album.clear()
        self.artwork_manager.current_art_url = None
        self.artwork_manager.art_cache.clear()
        self.artwork_manager.displayed_art_url = None

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

            if art:
                self.artwork_manager.load_art(art, self.current, self.album)

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
            art_data = self.artwork_manager.get_album_art_from_file(file_path)
            if art_data:
                pixmap = QPixmap()
                pixmap.loadFromData(art_data)
                self.album.setPixmap(pixmap)

            # Sonos cannot access local filesystem paths directly.
            # A temporary HTTP server exposes the selected file so the speaker
            # can stream it using a normal URL.
            if self.server is None:
                self.server = LocalMusicServer(file_path.parent, self.port)
                self.server.start()

            elif self.server.folder != file_path.parent:
                self.server.stop()
                self.server = LocalMusicServer(file_path.parent, self.port)
                self.server.start()

            # Build URL
            from urllib.parse import quote

            ip = get_local_ip()
            url = f"http://{ip}:{self.server.port}/{quote(filename)}"

            print("Playing:", url)

            # Play on Sonos
            self.current.play_uri(url)  # pyright: ignore[reportUnknownMemberType]

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

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

    def handle_play_pause(self) -> None:
        """
        Handle the Play/Pause button click event.

        Toggles playback on the selected speaker and updates the button label
        to reflect the current playback state.
        """
        if not self.current:
            QMessageBox.warning(self, "No speaker", "Select a room first")
            return

        self.playback_controller.play_pause()

        try:
            state = self.current.get_current_transport_info()["current_transport_state"]
            if state == "PLAYING":
                self.play_btn.setText("Pause")
            else:
                self.play_btn.setText("Play")
        except Exception:
            self.play_btn.setText("Play/Pause")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SonosApp()
    window.show()
    sys.exit(app.exec())
