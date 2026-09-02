# Tests for the ArtworkPanel UI component.
import sys

from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QApplication

from sonos_rescue.ui.artwork_panel import ArtworkPanel


def make_pixmap(color: str = "red") -> QPixmap:
    pixmap = QPixmap(10, 10)
    pixmap.fill(QColor(color))
    return pixmap


def test_artwork_panel_initial_state() -> None:
    """A newly created panel should show the default title and no artwork."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = ArtworkPanel()

    assert panel.title.text() == "No room selected"
    assert panel.artwork_label.pixmap().isNull()


def test_display_artwork_sets_pixmap() -> None:
    """display_artwork(pixmap) should show the given pixmap."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = ArtworkPanel()

    panel.display_artwork(make_pixmap())

    assert not panel.artwork_label.pixmap().isNull()


def test_display_artwork_none_clears_pixmap() -> None:
    """display_artwork(None) should clear any previously displayed artwork."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = ArtworkPanel()
    panel.display_artwork(make_pixmap())
    assert not panel.artwork_label.pixmap().isNull()

    panel.display_artwork(None)

    assert panel.artwork_label.pixmap().isNull()


def test_cleared_artwork_does_not_reappear_after_resize() -> None:
    """Cleared artwork should remain absent after the label is resized."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = ArtworkPanel()
    panel.display_artwork(make_pixmap())
    panel.display_artwork(None)
    panel.artwork_label.resize(500, 300)

    assert panel.artwork_label.pixmap().isNull()


def test_display_artwork_replaces_previous_pixmap() -> None:
    """Calling display_artwork again with a new pixmap should replace the old one."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    panel = ArtworkPanel()
    panel.display_artwork(make_pixmap("red"))
    first = panel.artwork_label.pixmap().toImage()

    panel.display_artwork(make_pixmap("blue"))
    second = panel.artwork_label.pixmap().toImage()

    assert first != second
