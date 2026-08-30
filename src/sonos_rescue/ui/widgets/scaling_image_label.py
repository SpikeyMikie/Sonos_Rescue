from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QResizeEvent
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QLabel, QWidget


class ScalingImageLabel(QLabel):
    """A QLabel that rescales its pixmap (keeping aspect ratio) to fill its current size."""

    def __init__(self, pixmap: QPixmap, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(400, 200)
        self.setScaledContents(False)
        self._original_pixmap = QPixmap()
        self.set_pixmap(pixmap)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Store the source pixmap and display it scaled to the current size."""
        self._original_pixmap = pixmap
        self._update_scaled_pixmap()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self._update_scaled_pixmap()

    def sizeHint(self) -> QSize:
        # Don't let the pixmap's native size dictate the layout's growth/shrink.
        return self.minimumSize()

    def minimumSizeHint(self) -> QSize:
        return self.minimumSize()

    def _update_scaled_pixmap(self) -> None:
        if self._original_pixmap.isNull():
            return
        scaled = self._original_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        super().setPixmap(scaled)
