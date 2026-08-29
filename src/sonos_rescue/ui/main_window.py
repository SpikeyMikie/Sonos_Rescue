from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidget,
)

import sys

# internal imports
from sonos_rescue.utils.resources import resource_path

# from rooms_panel import RoomsPanel
# from artwork_panel import ArtworkPanel
# from playlist_panel import PlaylistPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sonos Rescue")

        layout_main = QHBoxLayout()  # main layout
        layout_main.setContentsMargins(0, 0, 30, 0)

        # rooms_panel = RoomsPanel()
        # artwork_panel = ArtworkPanel()
        # playlist_panel = PlaylistPanel()

        rooms_panel = QWidget()  # Placeholder for RoomsPanel
        artwork_panel = QWidget()  # Placeholder for ArtworkPanel
        playlist_panel = QWidget()  # Placeholder for PlaylistPanel

        layout_main.addWidget(rooms_panel)
        layout_main.addWidget(artwork_panel)
        layout_main.addWidget(playlist_panel)

        container = QWidget()
        container.setLayout(layout_main)
        container.setAutoFillBackground(True)
        container.setStyleSheet("""
            background: transparent;
            color: #FFFFFF; font-size: 16px;
        """)
        self.setCentralWidget(container)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        toolbar.setIconSize(QSize(30, 30))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)

        refresh_pixmap = QPixmap(str(resource_path("icons/speaker-network.png")))
        refresh_pixmap = refresh_pixmap.scaled(
            100,
            100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        refresh_action = QAction(
            QIcon(refresh_pixmap),
            "&Find && Refresh",
            self,
        )
        refresh_action.setStatusTip("Find or Refresh the list of Speakers / Rooms")
        refresh_action.setShortcut(QKeySequence("Ctrl+f"))
        refresh_action.triggered.connect(self.button_clicked)
        toolbar.addAction(refresh_action)
        toolbar.addSeparator()

        play_local_pixmap = QPixmap(
            str(resource_path("icons/folder-open-document-music.png"))
        )
        play_local_pixmap = play_local_pixmap.scaled(
            100,
            100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        play_local_action = QAction(
            QIcon(play_local_pixmap),
            "Play Local File",
            self,
        )

        play_local_action.setStatusTip("Play a local music file")
        play_local_action.triggered.connect(self.button_clicked)
        toolbar.addAction(play_local_action)

        self.setStatusBar(QStatusBar(self))
        file_menu = self.menuBar().addMenu("&Menu")
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        file_menu.addAction(play_local_action)

    def button_clicked(self, checked: bool) -> None:
        print("click", checked)


# app_style = """
# QMainWindow {
#     background: qlineargradient(
#     x1: 0, y1: 0,
#     x2: 1, y2: 0,
#     stop: 0 #171E27,
#     stop: 0.2 #171E27,
#     stop: 1 #271817
# );
#     color: #FFFFFF;
#     font-size: 16px;
# }
# QToolBar {
#     background: qlineargradient(
#         x1: 0, y1: 0,
#         x2: 1, y2: 0,
#         stop: 0 #171E27,
#         stop: 0.2 #171E27,
#         stop: 1 #271817
#     );
#     color: #FFFFFF;
#     font-size: 16px;
#     border-bottom-color: #171E27;
#     border-left-color: #171E27;
#     border-right-color: #171E27;
#     border-top-color: #171E27;
#     border-width: 1px;
#     border-style: dashed;
# }
# QMenuBar {
#     background: qlineargradient(
#         x1: 0, y1: 0,
#         x2: 1, y2: 0,
#         stop: 0 #171E27,
#         stop: 1 #271817
#     );
#     color: #FFFFFF;
#     font-size: 16px;
# }
# QMenu {
#     background: qlineargradient(
#         x1: 0, y1: 0,
#         x2: 1, y2: 0,
#         stop: 0 #171E27,
#         stop: 1 #271817
#     );
#     color: #FFFFFF;
#     font-size: 16px;
# }"""

# Possible Highlight colours:
# pink - #CB64BF

# background-color: #171E27
# # complimentary background colours:
# # # 172627 dark teal
# # # 181727 dark purple
# # # 271817 dark red - used for gradient
# # # 262717 dark olive green

# app = QApplication(sys.argv)
# app.setStyleSheet(app_style)
# window = MainWindow()
# window.resize(600, 420)
# window.setMinimumHeight(420)
# window.show()
# app.exec()
