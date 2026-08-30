from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from .widgets.rainbow_frame import RainbowFrame
from .widgets.rainbow_background import RainbowBackground
from .widgets.scaling_image_label import ScalingImageLabel
from sonos_rescue.managers.artwork_manager import ArtworkManager, ArtworkDatabase


class ArtworkPanel(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        layout = main_layout
        layout.setContentsMargins(0, 0, 0, 0)

        artwork_rainbow_background = RainbowBackground(radius=16, alpha=20)
        artwork_rainbow_frame = RainbowFrame(
            border_width=1,
            glow_width=10,
            radius=16,
        )
        artwork_rainbow_background.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        artwork_rainbow_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        now_playing_label = QLabel("Now Playing")
        now_playing_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        now_playing_label.setFixedHeight(30)
        artwork_layout = QVBoxLayout(artwork_rainbow_frame)
        artwork_layout.setContentsMargins(10, 10, 10, 10)
        artwork_layout.addWidget(artwork_rainbow_background)

        artwork_content_layout = QVBoxLayout(artwork_rainbow_background)
        artwork_content_layout.setContentsMargins(0, 20, 0, 20)
        artwork_rainbow_background.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # get artwork from the ArtworkManager
        self.artwork_manager = ArtworkManager(ArtworkDatabase())
        self.artwork_label = ScalingImageLabel(
            QPixmap(self.artwork_manager.current_art_url or "")
        )
        self.artwork_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.artwork_label.setContentsMargins(20, 0, 20, 0)
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artwork_content_layout.addWidget(
            now_playing_label,
        )
        # no alignment here: it would size the label to its sizeHint instead of stretching it
        artwork_content_layout.addWidget(
            self.artwork_label,
            stretch=1,
        )
        self.layout().addWidget(artwork_rainbow_frame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def display_artwork(self, pixmap: QPixmap | None) -> None:
        """Update the displayed artwork, or clear it if pixmap is None."""
        if pixmap is None:
            self.artwork_label.clear()
            return

        self.artwork_label.set_pixmap(pixmap)
