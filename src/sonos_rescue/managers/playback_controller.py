from typing import Callable
from soco import SoCo  # type: ignore[import-untyped]


class PlaybackController:
    """
    Handles playback control for the selected Sonos speaker.

    This class provides methods to play, pause, skip tracks, and adjust
    volume on the currently selected speaker. It encapsulates the logic
    for interacting with the SoCo library and ensures that commands are
    only sent when a speaker is selected.
    """

    def __init__(self, get_current_speaker: Callable[[], SoCo | None]) -> None:
        """
        Initialise the playback controller.

        Args:
            get_current_speaker:
                A callable that returns the currently selected SoCo speaker,
                or None if no speaker is selected.
        """
        self.get_current_speaker = get_current_speaker

    def play_pause(self) -> None:
        """Toggle playback for the selected speaker."""
        current = self.get_current_speaker()
        if not current:
            return

        try:
            state = current.get_current_transport_info()["current_transport_state"]
            if state == "PLAYING":
                current.pause()
            else:
                current.play()  # pyright: ignore[reportUnknownMemberType]

        except Exception as e:
            print("Play/Pause error:", e)

    def next_track(self) -> None:
        """Skip to the next track."""
        current = self.get_current_speaker()
        if current:
            current.next()

    def prev_track(self) -> None:
        """Return to the previous track."""
        current = self.get_current_speaker()
        if current:
            current.previous()

    def set_volume(self, v: int) -> None:
        """Set the volume of the selected speaker."""
        current = self.get_current_speaker()
        if current:
            current.volume = v
