# Main window for the Sonos Rescue application

# Standard library imports
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

# third-party imports
from soco import SoCo  # pyright: ignore[reportMissingTypeStubs]

# gui imports
from PyQt6.QtCore import QSize, Qt, QThread, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QAction, QCloseEvent
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
from sonos_rescue.utils.network import get_local_ip
from sonos_rescue.utils.resources import resource_path
from sonos_rescue.managers.speaker_manager import SpeakerManager
from sonos_rescue.managers.artwork_manager import ArtworkManager, ArtResult
from sonos_rescue.services.local_music_server import LocalMusicServer
from sonos_rescue.ui.rooms_panel import RoomsPanel
from sonos_rescue.ui.artwork_panel import ArtworkPanel
from sonos_rescue.database.database import ArtworkDatabase
from sonos_rescue.ui.playlist_panel import PlaylistPanel
from sonos_rescue.managers.playback_controller import PlaybackController
from sonos_rescue.managers.playback_poller import NowPlayingUpdate
from sonos_rescue.managers.playback_poller import PlaybackPoller


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

        self.art_result: ArtResult | None = None
        self.artwork_panel = ArtworkPanel()
        self.playlist_panel = PlaylistPanel()
        self.rooms_panel = RoomsPanel(self.speaker_manager, self.playback_controller)
        self.speaker_manager.speaker_selected.connect(  # pyright: ignore[reportUnknownMemberType]
            self.display_selected_speaker
        )

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

        self.port: int = LocalMusicServer.DEFAULT_PORT
        self.server: LocalMusicServer | None = None

        # Start background refresh thread for the playback poller
        self.playback_poller = PlaybackPoller(
            get_current_speaker=lambda: self.current,
            artwork_manager=self.artwork_manager,
        )
        self.playback_poller_thread = QThread()
        self.playback_poller.moveToThread(self.playback_poller_thread)
        self.playback_poller_thread.started.connect(  # pyright: ignore[reportUnknownMemberType]
            self.playback_poller.run
        )
        QTimer.singleShot(  # pyright: ignore[reportUnknownMemberType]
            0, self.playback_poller_thread.start
        )  # Start the polling loop immediately
        self.playback_poller.now_playing_updated.connect(  # pyright: ignore[reportUnknownMemberType]
            self.apply_now_playing_update
        )

    def play_local_file(self) -> None:
        """Prompt for a local music file, then display its artwork and stream it."""
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select a music file",
            "",
            "Audio Files (*.mp3 *.flac *.wav *.m4a)",
        )
        if not file_path_str:
            return

        file_path = Path(file_path_str)
        self.display_local_artwork(file_path)
        self.stream_local_file(file_path)

    def display_local_artwork(self, file_path: Path) -> None:
        """Extract and display any embedded album artwork for a local file."""
        image_data = self.artwork_manager.get_album_art_from_file(file_path)
        pixmap = None
        if image_data is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
        self.artwork_panel.display_artwork(pixmap)

    def stream_local_file(self, file_path: Path) -> None:
        """Serve a local file over HTTP and instruct the selected speaker to play it."""
        if not self.current:
            QMessageBox.warning(self, "No speaker", "Select a room first")
            return

        try:
            # Sonos cannot access local filesystem paths directly, so a
            # temporary HTTP server exposes the file for the speaker to stream.
            if self.server is None or self.server.folder != file_path.parent:
                if self.server is not None:
                    self.server.stop()
                self.server = LocalMusicServer(file_path.parent, self.port)
                self.server.start()

            ip = get_local_ip()
            url = f"http://{ip}:{self.server.port}/{quote(file_path.name)}"

            self.current.play_uri(url)  # pyright: ignore[reportUnknownMemberType]

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_now_playing(self) -> None:
        """Trigger an immediate poll of the selected speaker."""
        if self.current:
            self.playback_poller.poll_once()

    def apply_now_playing_update(self, update: NowPlayingUpdate) -> None:
        """Apply a playback snapshot on the Qt main thread."""
        self.track_info.setText(f"{update.title}\n{update.artist}\n{update.album}")

        self.playlist_panel.queue.clear()
        for title in update.queue_titles:
            self.playlist_panel.queue.addItem(title)

        result = update.art_result
        if result is None or result.art_url is None or result.art_bytes is None:
            return

        if result.art_url == self.artwork_manager.displayed_art_url:
            return

        pixmap = self.artwork_manager.art_cache.get(result.art_url)
        if pixmap is None:
            pixmap = QPixmap()
            if not pixmap.loadFromData(result.art_bytes):
                return
            self.artwork_manager.art_cache[result.art_url] = pixmap
            if len(self.artwork_manager.art_cache) > self.artwork_manager.MAX_CACHE:
                self.artwork_manager.art_cache.pop(
                    next(iter(self.artwork_manager.art_cache))
                )

        self.artwork_manager.displayed_art_url = result.art_url
        self.artwork_manager.set_album_art(
            self.artwork_panel.artwork_label,
            pixmap,
        )

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

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle the window close event by stopping the playback poller."""
        poller = getattr(self, "playback_poller", None)
        if poller is not None:
            poller.stop()
            thread = poller.thread()
            if thread is not None:
                thread.quit()
                thread.wait()

        if self.server is not None:
            self.server.stop()

        if a0 is not None:
            a0.accept()


class QueueItemProtocol(Protocol):
    """
    Defines the minimum interface required for Sonos queue items.

    SoCo queue objects contain many attributes, but this application
    only requires the track title for displaying the queue.
    """

    title: str
