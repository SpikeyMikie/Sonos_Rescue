# Tests for the MainWindow UI component.
import sys
from types import SimpleNamespace
from typing import Any, cast

from PyQt6.QtWidgets import QApplication

from sonos_rescue.ui.main_window import MainWindow


def make_fake_speaker(
    player_name: str,
    queue_titles: list[str],
    track_info: dict[str, Any] | None = None,
) -> Any:
    info = track_info or {"title": "", "artist": "", "album": "", "album_art": None}
    queue_items = [SimpleNamespace(title=title) for title in queue_titles]
    return cast(
        Any,
        SimpleNamespace(
            player_name=player_name,
            get_current_track_info=lambda: info,
            get_queue=lambda: queue_items,
        ),
    )


def make_window() -> MainWindow:
    window = MainWindow()
    # Stop the background refresh thread so it can't mutate widgets from
    # another thread while a test is asserting against a fake speaker.
    # this will not be needed once the background refresh thread is properly managed in the MainWindow implementation.
    window.running = False
    return window


def queue_titles(window: MainWindow) -> list[str]:
    queue = window.playlist_panel.queue
    titles: list[str] = []
    for i in range(queue.count()):
        item = queue.item(i)
        assert item is not None
        titles.append(item.text())
    return titles


def test_selecting_speaker_populates_playlist_queue() -> None:
    """Emitting speaker_selected should populate the playlist queue with the speaker's queue titles."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    window = make_window()
    speaker = make_fake_speaker("Kitchen", ["Song A", "Song B"])

    window.speaker_manager.speaker_selected.emit(speaker)

    assert queue_titles(window) == ["Song A", "Song B"]


def test_selecting_new_speaker_replaces_previous_queue() -> None:
    """Selecting a different speaker should clear the old queue and show the new one."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    window = make_window()
    speaker1 = make_fake_speaker("Kitchen", ["Old Song"])
    speaker2 = make_fake_speaker("Bedroom", ["New Song"])

    window.display_selected_speaker(speaker1)
    assert queue_titles(window) == ["Old Song"]

    window.display_selected_speaker(speaker2)
    assert queue_titles(window) == ["New Song"]


def test_display_selected_speaker_updates_title_and_track_info() -> None:
    """Selecting a speaker should update the artwork title and now-playing track info."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    window = make_window()
    speaker = make_fake_speaker(
        "Kitchen",
        [],
        track_info={
            "title": "Track Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "album_art": None,
        },
    )

    window.display_selected_speaker(speaker)

    assert window.artwork_panel.title.text() == "Kitchen"
    assert window.track_info.text() == "Track Title\nArtist Name\nAlbum Name"


def test_update_now_playing_does_not_raise_on_speaker_error() -> None:
    """An error retrieving track/queue info should be swallowed, not crash the app."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    window = make_window()

    def raise_error() -> dict[str, Any]:
        raise Exception("speaker unreachable")

    window.current = cast(
        Any,
        SimpleNamespace(
            player_name="Kitchen",
            get_current_track_info=raise_error,
            get_queue=lambda: cast(list[Any], []),
        ),
    )

    window.update_now_playing()  # should not raise
