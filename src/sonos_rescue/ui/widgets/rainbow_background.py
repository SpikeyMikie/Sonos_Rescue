from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPaintEvent, QPainter, QConicalGradient, QColor
from PyQt6.QtWidgets import QWidget


class RainbowBackground(QWidget):
    """
    A widget that fills its whole area with a translucent rainbow gradient.
    parameters:
    - radius: the corner radius of the background.
    - alpha: the translucency of the background (0 fully transparent, 255 fully opaque).
    """

    def __init__(
        self, parent: QWidget | None = None, radius: int = 12, alpha: int = 150
    ):
        super().__init__(parent)
        self.radius = radius
        self.alpha = alpha

    def set_alpha(self, alpha: int) -> None:
        """Update the background translucency and repaint."""
        self.alpha = alpha
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        gradient = self._create_gradient(rect, alpha=self.alpha)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, self.radius, self.radius)

    def _create_gradient(
        self,
        rect: QRectF,
        alpha: int = 255,
    ) -> QConicalGradient:
        """Create the rainbow gradient used by the background."""

        gradient = QConicalGradient(
            rect.center(),
            0,
        )

        colours = (
            "#ff0000",
            "#ff8000",
            "#ffff00",
            "#00ff00",
            "#00ffff",
            "#0080ff",
            "#8000ff",
            "#ff00ff",
            "#ff0000",
        )

        for index, colour in enumerate(colours):
            qcolor = QColor(colour)
            qcolor.setAlpha(alpha)

            gradient.setColorAt(
                index / (len(colours) - 1),
                qcolor,
            )

        return gradient
