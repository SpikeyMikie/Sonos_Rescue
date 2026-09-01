# tests for transport controls in the Sonos Rescue application

import sys
from typing import cast

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap

from sonos_rescue.managers.playback_controller import PlaybackController
from sonos_rescue.ui.transport_controls import TransportControls
from sonos_rescue.utils.resources import resource_path


class FakePlaybackController:
    """Records calls instead of talking to a real Sonos speaker."""

    def __init__(self) -> None:
        self.play_pause_calls = 0
        self.prev_track_calls = 0
        self.next_track_calls = 0
        self.toggle_mute_calls = 0
        self.set_volume_calls = 0

    def play_pause(self) -> None:
        self.play_pause_calls += 1

    def prev_track(self) -> None:
        self.prev_track_calls += 1

    def next_track(self) -> None:
        self.next_track_calls += 1

    def toggle_mute(self) -> None:
        self.toggle_mute_calls += 1

    def set_volume(self, v: int) -> None:
        self.set_volume_calls += 1


def test_play_pause_button_toggle_calls_play_pause() -> None:
    """Toggling the play/pause button should call playback_controller.play_pause() once."""

    # app doesn't need to be accessed in this test, just needs to exist for PyQt widgets to be created
    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    fake_controller = FakePlaybackController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    controls.play_pause_button.toggle()

    assert fake_controller.play_pause_calls == 1


def test_prev_track_button_calls_prev_track() -> None:
    """Clicking the previous track button should call playback_controller.prev_track()."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    fake_controller = FakePlaybackController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    controls.previous_button.click()

    assert fake_controller.prev_track_calls == 1


def test_next_track_button_calls_next_track() -> None:
    """Clicking the next track button should call playback_controller.next_track()."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    fake_controller = FakePlaybackController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    controls.next_button.click()

    assert fake_controller.next_track_calls == 1


def test_toggle_mute_button_calls_toggle_mute() -> None:
    """Clicking the toggle mute button should call playback_controller.toggle_mute()."""

    # app is needed here to create the TransportControls widget but not accessed directly
    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    fake_controller = FakePlaybackController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    controls.mute_button.click()

    assert fake_controller.toggle_mute_calls == 1


def test_volume_slider_calls_set_volume() -> None:
    """Changing the volume slider should call playback_controller.set_volume()."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    fake_controller = FakePlaybackController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    controls.volume_slider.setValue(75)

    assert fake_controller.set_volume_calls == 1


def test_volume_slider_calls_set_volume_multiple_times() -> None:
    """Changing the volume slider multiple times should call playback_controller.set_volume() each time, with the correct values."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    class FakeVolumeController(FakePlaybackController):
        def __init__(self) -> None:
            super().__init__()
            self.set_volume_calls = 0
            self.volumes_received: list[int] = []

        def set_volume(self, v: int) -> None:
            self.set_volume_calls += 1
            self.volumes_received.append(v)

    fake_controller = FakeVolumeController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    controls.volume_slider.setValue(10)
    controls.volume_slider.setValue(50)
    controls.volume_slider.setValue(99)

    assert fake_controller.set_volume_calls == 3
    assert fake_controller.volumes_received == [10, 50, 99]


def test_update_play_pause_icon_changes_correctly() -> None:
    """The play/pause button icon should update correctly based on playback state."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    class FakePlayPauseController(FakePlaybackController):
        def __init__(self) -> None:
            super().__init__()
            self.is_playing = False

        def play_pause(self) -> None:
            self.play_pause_calls += 1
            self.is_playing = not self.is_playing

    fake_controller = FakePlayPauseController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    def expected_pixmap(icon_name: str) -> QPixmap:
        return QPixmap(str(resource_path(icon_name))).scaled(
            controls.ICON_SIZE, controls.ICON_SIZE
        )

    def current_pixmap() -> QPixmap:
        size = QSize(controls.ICON_SIZE, controls.ICON_SIZE)
        return controls.play_pause_button.icon().pixmap(size)

    # Initially should show play icon
    assert current_pixmap().toImage() == expected_pixmap("icons/control.png").toImage()

    # Simulate clicking the play button
    controls.play_pause_button.click()
    assert fake_controller.is_playing is True
    assert (
        current_pixmap().toImage()
        == expected_pixmap("icons/control-pause.png").toImage()
    )

    # Simulate clicking the pause button
    controls.play_pause_button.click()
    assert fake_controller.is_playing is False
    assert current_pixmap().toImage() == expected_pixmap("icons/control.png").toImage()


def test_toggle_mute_changes_icon_and_disables_volume_slider() -> None:
    """Toggling the mute button should update the icon and disable/enable the volume slider."""

    app = (  # pyright: ignore[reportUnusedVariable]
        QApplication.instance() or QApplication(sys.argv)
    )

    class FakeMuteController(FakePlaybackController):
        def __init__(self) -> None:
            super().__init__()
            self.is_muted = False

        def toggle_mute(self) -> None:
            self.toggle_mute_calls += 1
            self.is_muted = not self.is_muted

    fake_controller = FakeMuteController()
    controls = TransportControls(cast(PlaybackController, fake_controller))

    def expected_pixmap(icon_name: str) -> QPixmap:
        return QPixmap(str(resource_path(icon_name))).scaled(
            controls.ICON_SIZE, controls.ICON_SIZE
        )

    def current_pixmap() -> QPixmap:
        size = QSize(controls.ICON_SIZE, controls.ICON_SIZE)
        return controls.mute_button.icon().pixmap(size)

    # Initially should show unmuted icon and volume slider enabled
    assert (
        current_pixmap().toImage()
        == expected_pixmap("icons/speaker-volume.png").toImage()
    )
    assert controls.volume_slider.isEnabled() is True

    # Simulate clicking the mute button
    controls.mute_button.click()
    assert fake_controller.is_muted is True
    assert (
        current_pixmap().toImage()
        == expected_pixmap("icons/speaker-volume-control-mute.png").toImage()
    )
    assert controls.volume_slider.isEnabled() is False

    # Simulate clicking the unmute button
    controls.mute_button.click()
    assert fake_controller.is_muted is False
    assert (
        current_pixmap().toImage()
        == expected_pixmap("icons/speaker-volume.png").toImage()
    )
    assert controls.volume_slider.isEnabled() is True
