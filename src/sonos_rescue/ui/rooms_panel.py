from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from sonos_rescue.managers.playback_controller import PlaybackController
from sonos_rescue.managers.speaker_manager import SpeakerManager
from sonos_rescue.ui.room_card import RoomCard
from soco import SoCo  # type: ignore[import-untyped]


class RoomsPanel(QWidget):
    HEADER_HEIGHT = 30
    PANEL_SPACING = 0
    CARD_SPACING = 0
    TOP_MARGIN = 30

    def __init__(
        self,
        speaker_manager: SpeakerManager,
        playback_controller: PlaybackController,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.speaker_manager = speaker_manager
        self.playback_controller = playback_controller
        self.selected_room_card: RoomCard | None = None

        self.setFixedWidth(500)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.panel_layout = QVBoxLayout()
        self.setLayout(self.panel_layout)
        self.panel_layout.setContentsMargins(30, self.TOP_MARGIN, 30, 0)
        self.panel_layout.setSpacing(self.PANEL_SPACING)

        self._build_header()
        self._build_scroll_area()

        # React to speaker discovery
        self.speaker_manager.speakers_discovered.connect(  # pyright: ignore[reportUnknownMemberType]
            self.display_speakers
        )

        # populate immediately if speakers already discovered
        if self.speaker_manager.speakers:
            self.display_speakers(self.speaker_manager.speakers)

    def _build_header(self) -> None:
        room_label_header = QLabel("Speakers / Rooms")
        room_label_header.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        room_label_header.setFixedHeight(self.HEADER_HEIGHT)
        self.panel_layout.addWidget(room_label_header)

    def _build_scroll_area(self) -> None:
        self.rooms_scroll = QScrollArea()
        self.rooms_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.rooms_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.rooms_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.rooms_scroll.setWidgetResizable(True)
        self.rooms_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.rooms_content_widget = QWidget()
        self.rooms_content_layout = QVBoxLayout(self.rooms_content_widget)
        self.rooms_content_layout.setContentsMargins(0, 0, 0, 0)
        self.rooms_content_layout.setSpacing(self.CARD_SPACING)

        self.rooms_scroll.setWidget(self.rooms_content_widget)
        self.panel_layout.addWidget(self.rooms_scroll)

    def display_speakers(self, speakers: list[SoCo]) -> None:
        """Rebuild the room cards from the discovered speakers list."""
        # clear old cards
        for i in reversed(range(self.rooms_content_layout.count())):
            item = self.rooms_content_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                widget.setParent(None)

        self.selected_room_card = None

        # add new cards
        for speaker in speakers:
            room_name = getattr(speaker, "player_name", "Unknown Room")
            card = RoomCard(
                room_name,
                speaker,
                self.speaker_manager.select_speaker,
                self.playback_controller,
            )
            card.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
                lambda c=card: self._room_selected(c)
            )
            self.rooms_content_layout.addWidget(
                card, alignment=Qt.AlignmentFlag.AlignVCenter
            )

        self.rooms_content_widget.adjustSize()

    def _room_selected(self, room_card: RoomCard) -> None:
        if self.selected_room_card is not None:
            self.selected_room_card.set_selected(False)
        room_card.set_selected(True)
        self.selected_room_card = room_card
