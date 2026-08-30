from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidget,
)

# internal imports
from sonos_rescue.utils.resources import resource_path
from sonos_rescue.managers.speaker_manager import SpeakerManager

from sonos_rescue.ui.rooms_panel import RoomsPanel


class MainWindow(QMainWindow):
    def __init__(self, parent: QMainWindow | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sonos Rescue")

        self.speaker_manager = SpeakerManager()

        layout_main = QHBoxLayout()
        layout_main.setContentsMargins(0, 0, 30, 0)

        # rooms_panel = RoomsPanel()
        # artwork_panel = ArtworkPanel()
        # playlist_panel = PlaylistPanel()

        rooms_panel = RoomsPanel(self.speaker_manager)
        artwork_panel = QWidget()  # Placeholder for ArtworkPanel
        playlist_panel = QWidget()  # Placeholder for PlaylistPanel

        layout_main.addWidget(rooms_panel)
        layout_main.addWidget(artwork_panel)
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
            self.button_clicked
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

    def button_clicked(self, checked: bool) -> None:
        print("click", checked)
