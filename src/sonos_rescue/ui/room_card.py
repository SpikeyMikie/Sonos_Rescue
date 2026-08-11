# Standard library
from typing import Callable

# Type checking exceptions
import soco  # type: ignore[import-untyped]
from soco import SoCo  # type: ignore[import-untyped]

# GUI framework
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QPushButton,
)


class RoomCard(QFrame):
    """
    A GUI card representing a Sonos speaker.

    Displays basic information about a discovered speaker and provides a
    button that allows the user to select it for control. Multiple
    RoomCard widgets can be displayed together to create a list of
    available Sonos devices on the network.
    """

    def __init__(self, speaker: SoCo, on_select: Callable[[SoCo], None]) -> None:
        """
        Initialise a room card for a Sonos speaker.

        Args:
            speaker:
                The SoCo speaker instance represented by this card.
            on_select:
                Callback function executed when the user selects the
                speaker for control.
        """
        super().__init__()
        self.speaker: SoCo = speaker
        self.on_select: Callable[[SoCo], None] = on_select

        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("padding:10px; margin:5px; border-radius:8px;")

        layout = QVBoxLayout()

        self.name_label = QLabel(speaker.player_name)
        self.status_label = QLabel("Idle")

        self.control_button = QPushButton("Control")
        self.control_button.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self.select
        )

        layout.addWidget(self.name_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.control_button)

        self.setLayout(layout)

    def select(self) -> None:
        """
        Notify the parent application that this speaker has been selected.

        Invokes the callback (created in init), passing the
        associated instance.
        """
        self.on_select(self.speaker)
