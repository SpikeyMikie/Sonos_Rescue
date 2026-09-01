from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QWidget
from sonos_rescue.utils.resources import resource_path
from sonos_rescue.managers.playback_controller import PlaybackController


class TransportControls(QWidget):
    ICON_SIZE = 32

    def __init__(self, playback_controller: PlaybackController):
        super().__init__()

        self.playback_controller = playback_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.play_pause_button = self.create_icon_button(
            str(resource_path("icons/control.png"))
        )
        self.play_pause_button.setCheckable(True)
        self.play_pause_button.toggled.connect(  # pyright: ignore[reportUnknownMemberType]
            self.update_play_pause_icon
        )
        self.play_pause_button.toggled.connect(  # pyright: ignore[reportUnknownMemberType]
            self._on_play_pause_toggled
        )
        self.play_pause_button.setStatusTip("Play / Pause the current track")

        self.previous_button = self.create_icon_button(
            str(resource_path("icons/control-skip-180.png"))
        )
        self.next_button = self.create_icon_button(
            str(resource_path("icons/control-skip.png"))
        )

        for button in (
            self.play_pause_button,
            self.previous_button,
            self.next_button,
        ):
            buttons_layout.addWidget(button)

        self.previous_button.setStatusTip("Play the previous track")
        self.previous_button.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self._on_prev_clicked
        )
        self.next_button.setStatusTip("Play the next track")
        self.next_button.clicked.connect(  # pyright: ignore[reportUnknownMemberType]
            self._on_next_clicked
        )

        volume_layout = QHBoxLayout()

        self.mute_button = self.create_icon_button(
            str(resource_path("icons/speaker-volume.png"))
        )
        self.mute_button.setCheckable(True)
        self.mute_button.toggled.connect(  # pyright: ignore[reportUnknownMemberType]
            self.toggle_mute
        )
        self.mute_button.toggled.connect(  # pyright: ignore[reportUnknownMemberType]
            self._on_mute_toggled
        )
        self.mute_button.setStatusTip("Mute / Unmute the volume")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(30)
        self.volume_slider.setSingleStep(3)
        self.volume_slider.setStatusTip("Adjust the volume level")
        self.volume_slider.valueChanged.connect(  # pyright: ignore[reportUnknownMemberType]
            self.playback_controller.set_volume
        )

        volume_layout.addWidget(self.mute_button)
        volume_layout.addWidget(self.volume_slider)

        layout.addLayout(buttons_layout)
        layout.addLayout(volume_layout)

    def create_icon_button(self, icon_file: str) -> QPushButton:
        button = QPushButton()
        button.setFixedSize(40, 40)
        button.setIcon(
            QIcon(
                QPixmap(icon_file).scaled(
                    self.ICON_SIZE,
                    self.ICON_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            )
        )
        button.setStyleSheet("border: none;")
        return button

    def update_play_pause_icon(self, playing: bool) -> None:
        icon_file = (
            str(resource_path("icons/control.png"))
            if playing
            else str(resource_path("icons/control-pause.png"))
        )
        self.play_pause_button.setIcon(
            QIcon(
                QPixmap(icon_file).scaled(
                    self.ICON_SIZE,
                    self.ICON_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            )
        )

    def toggle_mute(self, muted: bool) -> None:
        self.volume_slider.setEnabled(not muted)

        icon_file = (
            str(resource_path("icons/speaker-volume-control-mute.png"))
            if muted
            else str(resource_path("icons/speaker-volume.png"))
        )
        self.mute_button.setIcon(
            QIcon(
                QPixmap(icon_file).scaled(
                    self.ICON_SIZE,
                    self.ICON_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            )
        )

    def _on_play_pause_toggled(self, _checked: bool) -> None:
        self.playback_controller.play_pause()

    def _on_prev_clicked(self, _checked: bool) -> None:
        self.playback_controller.prev_track()

    def _on_next_clicked(self, _checked: bool) -> None:
        self.playback_controller.next_track()

    def _on_mute_toggled(self, _checked: bool) -> None:
        self.playback_controller.toggle_mute()
