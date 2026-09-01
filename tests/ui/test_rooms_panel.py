# Tests for the RoomPanel UI component.
import sys
from types import SimpleNamespace
from typing import Any, cast

from PyQt6.QtWidgets import QApplication

from sonos_rescue.managers.playback_controller import PlaybackController
from sonos_rescue.managers.speaker_manager import SpeakerManager
from sonos_rescue.ui.room_card import RoomCard
from sonos_rescue.ui.rooms_panel import RoomsPanel


def make_speaker(player_name: str) -> Any:
    return cast(Any, SimpleNamespace(player_name=player_name))


def make_panel(speaker_manager: SpeakerManager | None = None) -> RoomsPanel:
    manager = speaker_manager or SpeakerManager()
    controller = PlaybackController(lambda: manager.current)
    return RoomsPanel(manager, controller)


def room_cards(panel: RoomsPanel) -> list[RoomCard]:
    layout = panel.rooms_content_layout
    return [
        widget
        for i in range(layout.count())
        if isinstance(widget := layout.itemAt(i).widget(), RoomCard)  # type: ignore[union-attr]
    ]


def test_display_speakers_creates_one_card_per_speaker() -> None:
    """display_speakers should add one RoomCard per speaker, labelled with its room name."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = make_panel()
    speakers = [make_speaker("Kitchen"), make_speaker("Bedroom")]

    panel.display_speakers(speakers)

    cards = room_cards(panel)
    assert [card.room_label.text() for card in cards] == ["Kitchen", "Bedroom"]


def test_display_speakers_uses_unknown_room_fallback() -> None:
    """A speaker without a player_name should be labelled 'Unknown Room'."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = make_panel()
    speaker_without_name = cast(Any, SimpleNamespace())

    panel.display_speakers([speaker_without_name])

    cards = room_cards(panel)
    assert cards[0].room_label.text() == "Unknown Room"


def test_display_speakers_clears_old_cards_on_rebuild() -> None:
    """Calling display_speakers again should remove cards from the previous call."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = make_panel()
    panel.display_speakers([make_speaker("Kitchen"), make_speaker("Bedroom")])
    assert len(room_cards(panel)) == 2

    panel.display_speakers([make_speaker("Office")])

    cards = room_cards(panel)
    assert [card.room_label.text() for card in cards] == ["Office"]


def test_panel_populates_immediately_if_speakers_already_discovered() -> None:
    """If speaker_manager already has speakers, the panel should show cards without waiting for the signal."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    manager = SpeakerManager()
    manager.speakers = [make_speaker("Kitchen")]

    panel = make_panel(manager)

    cards = room_cards(panel)
    assert [card.room_label.text() for card in cards] == ["Kitchen"]


def test_speakers_discovered_signal_triggers_display_speakers() -> None:
    """Emitting speakers_discovered after construction should rebuild the cards."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    manager = SpeakerManager()
    panel = make_panel(manager)
    assert room_cards(panel) == []

    manager.speakers_discovered.emit([make_speaker("Kitchen")])

    cards = room_cards(panel)
    assert [card.room_label.text() for card in cards] == ["Kitchen"]


def test_clicking_a_card_selects_it() -> None:
    """Emitting a card's clicked signal should mark it selected on the panel."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = make_panel()
    panel.display_speakers([make_speaker("Kitchen")])
    card = room_cards(panel)[0]

    card.clicked.emit()

    assert panel.selected_room_card is card
    assert card.selected is True


def test_selecting_a_new_card_deselects_the_previous_one() -> None:
    """Selecting a second card should deselect the first."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = make_panel()
    panel.display_speakers([make_speaker("Kitchen"), make_speaker("Bedroom")])
    card1, card2 = room_cards(panel)

    card1.clicked.emit()
    card2.clicked.emit()

    assert card1.selected is False
    assert card2.selected is True
    assert panel.selected_room_card is card2


def test_display_speakers_resets_selection() -> None:
    """Rebuilding the card list should clear any previous selection."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = make_panel()
    panel.display_speakers([make_speaker("Kitchen")])
    room_cards(panel)[0].clicked.emit()
    assert panel.selected_room_card is not None

    panel.display_speakers([make_speaker("Bedroom")])

    assert panel.selected_room_card is None


def test_display_speakers_passes_playback_controller_to_cards() -> None:
    """Each card's transport_controls should receive the panel's playback_controller."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    manager = SpeakerManager()
    controller = PlaybackController(lambda: manager.current)
    panel = RoomsPanel(manager, controller)
    panel.display_speakers([make_speaker("Kitchen")])

    card = room_cards(panel)[0]
    assert card.transport_controls.playback_controller is controller
