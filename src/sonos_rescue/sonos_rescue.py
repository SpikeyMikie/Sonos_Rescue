"""
Main entry point for the Sonos Rescue application.
"""

# Standard library
import sys

# GUI framework
from PyQt6.QtWidgets import (
    QApplication,
)

# internal app imports
from .ui.main_window import MainWindow


def main() -> None:
    """
    Entry point for the Sonos Rescue application.

    Create the QApplication instance, initialise the main window,
    and start the event loop.
    """
    app_style = """
    QMainWindow {
        background: qlineargradient(
        x1: 0, y1: 0,
        x2: 1, y2: 0,
        stop: 0 #171E27,
        stop: 0.2 #171E27,
        stop: 1 #271817
    );
        color: #FFFFFF;
        font-size: 16px;
    }
    QToolBar {
        background: qlineargradient(
            x1: 0, y1: 0,
            x2: 1, y2: 0,
            stop: 0 #171E27,
            stop: 0.2 #171E27,
            stop: 1 #271817
        );
        color: #FFFFFF;
        font-size: 16px;
        border-bottom-color: #171E27;
        border-left-color: #171E27;
        border-right-color: #171E27;
        border-top-color: #171E27;
        border-width: 1px;
        border-style: dashed;
    }
    QMenuBar {
        background: qlineargradient(
            x1: 0, y1: 0,
            x2: 1, y2: 0,
            stop: 0 #171E27,
            stop: 1 #271817
        );
        color: #FFFFFF;
        font-size: 16px;
    }
    QMenu {
        background: qlineargradient(
            x1: 0, y1: 0,
            x2: 1, y2: 0,
            stop: 0 #171E27,
            stop: 1 #271817
        );
        color: #FFFFFF;
        font-size: 16px;
    }"""
    app = QApplication(sys.argv)
    app.setStyleSheet(app_style)

    window = MainWindow()
    window.resize(600, 420)
    window.setMinimumHeight(420)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
