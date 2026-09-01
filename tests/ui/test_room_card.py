from types import SimpleNamespace
from typing import Any, cast
from sonos_rescue.managers.playback_controller import PlaybackController
from sonos_rescue.ui.room_card import RoomCard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import QEvent, QPointF, Qt
import sys


def make_card(on_select: Any = lambda s: None) -> RoomCard:
    room_name = "TestRoom"
    speaker = cast(Any, SimpleNamespace(player_name="TestRoom"))

    def get_current_speaker() -> Any:
        return speaker

    return RoomCard(
        room_name,
        speaker,
        on_select,
        PlaybackController(get_current_speaker),
    )


def test_room_card_select_calls_set_selected() -> None:
    """Test that the `set_selected` method of `RoomCard` calls the provided `on_select` callback with the correct speaker."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )
    _called: dict[str, Any] = {}

    def on_select(s: Any) -> None:
        _called["s"] = s

    card = make_card(on_select=on_select)

    card.set_selected(True)
    assert _called["s"] is card.speaker
    assert card.selected is True
    card.set_selected(False)
    assert card.selected is False
    assert _called["s"] is card.speaker


def test_room_card_does_not_call_on_select_on_construction() -> None:
    """Constructing a RoomCard should not invoke on_select until set_selected is called."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    calls: list[Any] = []
    make_card(on_select=calls.append)

    assert calls == []


def test_room_card_sets_room_label_text() -> None:
    """The room_label should display the given room name."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    card = make_card()

    assert card.room_label.text() == "TestRoom"


def test_room_card_passes_playback_controller_to_transport_controls() -> None:
    """The given playback_controller should be forwarded to the embedded TransportControls."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    room_name = "TestRoom"
    speaker = cast(Any, SimpleNamespace(player_name="TestRoom"))

    def get_current_speaker() -> Any:
        return speaker

    controller = PlaybackController(get_current_speaker)
    card = RoomCard(room_name, speaker, lambda s: None, controller)

    assert card.transport_controls.playback_controller is controller


def test_room_card_set_selected_updates_border_width() -> None:
    """set_selected should widen the rainbow_frame border when selected and restore it when deselected."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    card = make_card()

    card.set_selected(True)
    assert card.rainbow_frame.border_width == card.selected_border_width

    card.set_selected(False)
    assert card.rainbow_frame.border_width == card.normal_border_width


def test_room_card_mouse_press_emits_clicked() -> None:
    """Pressing the mouse anywhere on the card should emit the clicked signal."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    card = make_card()
    emitted: list[bool] = []
    card.clicked.connect(lambda: emitted.append(True))

    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(0, 0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    card.mousePressEvent(event)

    assert emitted == [True]


def test_room_card_event_filter_emits_clicked_for_child_press() -> None:
    """A mouse press on a child widget should also emit clicked, via the installed event filter."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    card = make_card()
    emitted: list[bool] = []
    card.clicked.connect(lambda: emitted.append(True))

    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(0, 0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    card.eventFilter(card.room_label, event)

    assert emitted == [True]
