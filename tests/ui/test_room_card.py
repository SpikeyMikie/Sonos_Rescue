from types import SimpleNamespace
from typing import Any, cast
from sonos_rescue.ui.room_card import RoomCard
from PyQt6.QtWidgets import QApplication
import sys


def test_room_card_select_calls_on_select() -> None:
    """Test that the `select` method of `RoomCard` calls the provided `on_select` callback with the correct speaker."""

    # app doesn't need to be accessed in this test, just needs to exist for PyQt widgets to be created
    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    speaker = cast(Any, SimpleNamespace(player_name="TestRoom"))
    _called: dict[str, Any] = {}

    def on_select(s: Any) -> None:
        _called["s"] = s

    card = RoomCard(speaker, on_select)
    assert card.name_label.text() == "TestRoom"
    card.select()
    assert _called["s"] is speaker
