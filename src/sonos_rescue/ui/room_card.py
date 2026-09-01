from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QMouseEvent
from typing import Callable
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QObject
from soco import SoCo  # type: ignore[import-untyped]

from sonos_rescue.managers.playback_controller import PlaybackController

from .widgets.rainbow_frame import RainbowFrame
from .widgets.rainbow_background import RainbowBackground
from .transport_controls import TransportControls


class RoomCard(QWidget):
    clicked = pyqtSignal()
    CARD_HEIGHT = 250

    def __init__(
        self,
        room_name: str,
        speaker: SoCo,
        on_select: Callable[[SoCo], None],
        playback_controller: PlaybackController,
    ):
        super().__init__()

        self.on_select: Callable[[SoCo], None] = on_select
        self.speaker = speaker
        self.normal_border_width = 1
        self.selected_border_width = 4
        self.selected = False
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            background-color: transparent;
            border-radius: 10px;
            color: #FFFFFF;
            font-size: 16px;
        """)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        layout_rainbow_frame = RainbowFrame(
            border_width=self.normal_border_width,
            glow_width=10,
            radius=16,
        )
        self.rainbow_frame = layout_rainbow_frame
        main_layout.addWidget(layout_rainbow_frame)
        room_background = RainbowBackground(radius=16, alpha=20)
        frame_layout = QVBoxLayout(layout_rainbow_frame)
        frame_layout.setContentsMargins(10, 0, 10, 0)
        frame_layout.addWidget(room_background)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.room_label = QLabel(room_name)
        self.room_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.transport_controls = TransportControls(playback_controller)

        layout = QVBoxLayout(room_background)
        layout.addWidget(self.room_label)
        layout.addSpacing(20)
        layout.addWidget(self.transport_controls)
        layout.setContentsMargins(
            20, 40, 40, 40
        )  # added 20 to right side to account for the icon on volume slider
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        border_width = (
            self.selected_border_width if selected else self.normal_border_width
        )
        self.rainbow_frame.set_border_width(border_width)
        self.on_select(self.speaker)
        self.update()

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.clicked.emit()
        super().mousePressEvent(a0)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1 is not None and a1.type() == QEvent.Type.MouseButtonPress:
            self.clicked.emit()
        return super().eventFilter(a0, a1)
