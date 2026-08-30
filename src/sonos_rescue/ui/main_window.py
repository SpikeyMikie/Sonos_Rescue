from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidget,
)

# internal imports
from sonos_rescue.utils.resources import resource_path
from sonos_rescue.managers.speaker_manager import SpeakerManager
from sonos_rescue.managers.artwork_manager import ArtworkManager

from sonos_rescue.ui.rooms_panel import RoomsPanel
from sonos_rescue.ui.artwork_panel import ArtworkPanel
from sonos_rescue.database.database import ArtworkDatabase


class MainWindow(QMainWindow):
    def __init__(self, parent: QMainWindow | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sonos Rescue")

        self.speaker_manager = SpeakerManager()
        self.artwork_manager = ArtworkManager(ArtworkDatabase())

        layout_main = QHBoxLayout()
        layout_main.setContentsMargins(0, 0, 30, 0)

        self.artwork_panel = ArtworkPanel()
        playlist_panel = QWidget()  # Placeholder for PlaylistPanel

        rooms_panel = RoomsPanel(self.speaker_manager)

        layout_main.addWidget(rooms_panel)
        layout_main.addWidget(self.artwork_panel)
        layout_main.addWidget(playlist_panel)

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
        # this only lets us test artwork extraction/display for now.
