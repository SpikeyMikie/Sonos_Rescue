from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QPen, QConicalGradient, QColor, QPaintEvent
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt


class RainbowFrame(QFrame):
    """A QFrame with a soft glowing rainbow border."""

    def __init__(
        self,
        parent: QFrame | None = None,
        border_width: int = 30,
        glow_width: int = 10,
        radius: int = 12,
    ) -> None:
        super().__init__(parent)

        self.border_width = border_width
        self.glow_width = glow_width
        self.radius = radius

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_border_width(self, border_width: int) -> None:
        self.border_width = border_width
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(
            self.glow_width,
            self.glow_width,
            -self.glow_width,
            -self.glow_width,
        )

        gradient = self._create_gradient(rect)

        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Soft glow
        for width in range(self.glow_width, 0, -2):
            alpha = int(50 * (1 - width / self.glow_width))

            glow_gradient = self._create_gradient(
                rect,
                alpha=alpha,
            )

            painter.setPen(
                QPen(
                    glow_gradient,
                    width,
                )
            )

            glow_rect = rect.adjusted(
                width / 2,
                width / 2,
                -width / 2,
                -width / 2,
            )

            painter.drawRoundedRect(
                glow_rect,
                self.radius,
                self.radius,
            )

        # Bright border
        painter.setPen(
            QPen(
                gradient,
                self.border_width,
            )
        )

        border_rect = rect.adjusted(
            self.border_width / 2,
            self.border_width / 2,
            -self.border_width / 2,
            -self.border_width / 2,
        )

        painter.drawRoundedRect(
            border_rect,
            self.radius,
            self.radius,
        )

    def _create_gradient(
        self,
        rect: QRectF,
        alpha: int = 255,
    ) -> QConicalGradient:
        """Create the rainbow gradient used by the border."""

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
