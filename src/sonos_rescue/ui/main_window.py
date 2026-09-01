# Main window for the Sonos Rescue application

# Standard library imports
from typing import Protocol, cast
from time import sleep
import threading

# third-party imports
from soco import SoCo  # pyright: ignore[reportMissingTypeStubs]

# gui imports
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidget,
    QMessageBox,
    QInputDialog,
)

# internal imports
from sonos_rescue.utils.resources import resource_path
from sonos_rescue.managers.speaker_manager import SpeakerManager
from sonos_rescue.managers.artwork_manager import ArtworkManager

from sonos_rescue.ui.rooms_panel import RoomsPanel
from sonos_rescue.ui.artwork_panel import ArtworkPanel
from sonos_rescue.database.database import ArtworkDatabase
from sonos_rescue.managers.playback_controller import PlaybackController
from sonos_rescue.ui.playlist_panel import PlaylistPanel


class MainWindow(QMainWindow):
    def __init__(self, parent: QMainWindow | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sonos Rescue")

        self.speaker_manager = SpeakerManager()
        self.artwork_manager = ArtworkManager(ArtworkDatabase())

        self.track_info = QLabel("")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album = QLabel("")

        layout_main = QHBoxLayout()
        layout_main.setContentsMargins(0, 0, 30, 0)

        self.current: SoCo | None = None
        self.playback_controller = PlaybackController(
            get_current_speaker=lambda: self.current
        )

        self.artwork_panel = ArtworkPanel()
        self.playlist_panel = PlaylistPanel()
        self.rooms_panel = RoomsPanel(self.speaker_manager, self.playback_controller)
        self.speaker_manager.speaker_selected.connect(self.display_selected_speaker)

        layout_main.addWidget(self.rooms_panel)
        layout_main.addWidget(self.artwork_panel)
        layout_main.addWidget(self.playlist_panel)

        container = QWidget()
        container.setLayout(layout_main)
        container.setAutoFillBackground(True)
        container.setStyleSheet("""
            background: transparent;
            color: #FFFFFF; font-size: 16px;
        """)
        self.setCentralWidget(container)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        toolbar.setIconSize(QSize(30, 30))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)

        refresh_pixmap = QPixmap(str(resource_path("icons/speaker-network.png")))
        refresh_pixmap = refresh_pixmap.scaled(
            100,
            100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        refresh_action = QAction(
            QIcon(refresh_pixmap),
            "&Find && Refresh",
            self,
        )
        refresh_action.setStatusTip("Find or Refresh the list of Speakers / Rooms")
        refresh_action.setShortcut(QKeySequence("Ctrl+f"))
        refresh_action.triggered.connect(  # pyright: ignore[reportUnknownMemberType]
            self.speaker_manager.discover_speakers
        )
        toolbar.addAction(refresh_action)  # pyright: ignore[reportUnknownMemberType]
        toolbar.addSeparator()

        play_local_pixmap = QPixmap(
            str(resource_path("icons/folder-open-document-music.png"))
        )
        play_local_pixmap = play_local_pixmap.scaled(
            100,
            100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        play_local_action = QAction(
            QIcon(play_local_pixmap),
            "Play Local File",
            self,
        )

        play_local_action.setStatusTip("Play a local music file")
        play_local_action.triggered.connect(  # pyright: ignore[reportUnknownMemberType]
            self.play_local_file
        )
        toolbar.addAction(play_local_action)  # pyright: ignore[reportUnknownMemberType]

        self.setStatusBar(QStatusBar(self))
        file_menu = self.menuBar()
        assert file_menu is not None  # to satisfy pyright
        menu = file_menu.addMenu("&Menu")
        assert menu is not None  # to satisfy pyright
        menu.addAction(refresh_action)  # pyright: ignore[reportUnknownMemberType]
        menu.addSeparator()  # pyright: ignore[reportUnknownMemberType]
        menu.addAction(play_local_action)  # pyright: ignore[reportUnknownMemberType]

        self.title = QLabel("No room selected")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:18px;")

        # Start background refresh thread
        self.running = True
        threading.Thread(target=self.refresh_loop, daemon=True).start()

    def play_local_file(self) -> None:
        # Implement the logic to play a local music file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a music file",
            "",
            "Audio Files (*.mp3 *.flac *.wav *.m4a)",
        )
        if not file_path:
            return

        image_data = self.artwork_manager.get_album_art_from_file(file_path)
        pixmap = None
        if image_data is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
        self.artwork_panel.display_artwork(pixmap)

        # TODO: actual playback (streaming to Sonos) is a separate step —
        # this only lets us test artwork extraction/display for now

    def refresh_loop(self) -> None:
        """
        Background worker that refreshes playback information (every 2 secs).

        Runs in a daemon thread, for the lifetime of the application.
        """
        while self.running:
            try:
                self.update_now_playing()
            except Exception as e:
                print("Refresh error:", e)
            sleep(2)

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
                self.artwork_manager.load_art(art, self.current, self.artwork_panel)

            # update queue (lightweight)
            q = cast(list[QueueItemProtocol], self.current.get_queue())
            self.playlist_panel.queue.clear()

            for item in q:
                self.playlist_panel.queue.addItem(item.title)

        except Exception as e:
            print("Now playing update error:", e)

    def display_selected_speaker(self, speaker: SoCo) -> None:
        """Update the GUI to reflect the currently selected Sonos speaker."""
        self.current = speaker
        self.artwork_panel.title.setText(speaker.player_name)
        self.playlist_panel.queue.clear()
        self.update_now_playing()

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


class QueueItemProtocol(Protocol):
    """
    Defines the minimum interface required for Sonos queue items.

    SoCo queue objects contain many attributes, but this application
    only requires the track title for displaying the queue.
    """

    title: str
