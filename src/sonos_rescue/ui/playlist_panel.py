from PyQt6.QtWidgets import (
    QListWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from sonos_rescue.ui.widgets.rainbow_background import RainbowBackground
from sonos_rescue.ui.widgets.rainbow_frame import RainbowFrame


class PlaylistPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.panel_layout = QVBoxLayout()
        self.setLayout(self.panel_layout)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)

        self.playlist_rainbow_frame = RainbowFrame(
            border_width=1,
            glow_width=10,
            radius=16,
        )
        self.playlist_rainbow_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.playlist_rainbow_frame.setContentsMargins(0, 0, 0, 0)
        self.playlist_scrollable_area = QScrollArea()
        self.playlist_scrollable_area.setFrameShape(QFrame.Shape.NoFrame)
        self.playlist_scrollable_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.playlist_scrollable_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.playlist_scrollable_area.setWidgetResizable(True)
        self.playlist_scrollable_area.setWidget(self.playlist_rainbow_frame)

        self.panel_layout.addWidget(self.playlist_scrollable_area)
        self.setFixedWidth(500)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self.playlist_frame_layout = QVBoxLayout(self.playlist_rainbow_frame)
        self.playlist_frame_layout.setContentsMargins(10, 10, 10, 10)
        self.playlist_rainbow_background = RainbowBackground(radius=16, alpha=20)
        self.playlist_frame_layout.addWidget(self.playlist_rainbow_background)

        self.playlist_layout = QVBoxLayout(self.playlist_rainbow_background)
        self.playlist_layout.setContentsMargins(30, 20, 30, 20)

        self.playlist_label = QLabel("Playlist / Queue")
        self.playlist_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        self.queue: QListWidget = QListWidget()
        self.queue.setMinimumWidth(300)
        self.queue.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )

        self.playlist_label.setFixedHeight(30)
        self.playlist_layout.addWidget(self.playlist_label)
        self.playlist_layout.addWidget(self.queue)
