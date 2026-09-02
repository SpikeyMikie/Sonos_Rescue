# Tests for the PlaylistPanel UI component.
import sys

from PyQt6.QtWidgets import QApplication

from sonos_rescue.ui.playlist_panel import PlaylistPanel


def test_playlist_panel_initial_state() -> None:
    """A newly created panel should show the default label and an empty queue."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = PlaylistPanel()

    assert panel.playlist_label.text() == "Playlist / Queue"
    assert panel.queue.count() == 0


def test_playlist_panel_scroll_area_wraps_rainbow_frame() -> None:
    """The scroll area should host the rainbow frame that contains the queue."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = PlaylistPanel()

    assert panel.playlist_scrollable_area.widget() is panel.playlist_rainbow_frame
    assert panel.playlist_scrollable_area.widgetResizable() is True
