from dataclasses import dataclass
from typing import Callable
from soco import SoCo  # type: ignore[import-untyped]
from soco.exceptions import SoCoUPnPException  # type: ignore[import-untyped]

from sonos_rescue.managers.artwork_manager import ArtResult


@dataclass(frozen=True)
class NowPlayingUpdate:
    """Immutable playback snapshot passed from the refresh worker to Qt."""

    title: str
    artist: str
    album: str
    queue_titles: list[str]
    art_result: ArtResult | None


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
                return

            try:
                current.play()  # pyright: ignore[reportUnknownMemberType]
            except SoCoUPnPException as e:
                # error 701: nothing loaded as the transport source yet, fall back to the queue
                if str(e.error_code) == "701" and current.get_queue():
                    current.play_from_queue(
                        0
                    )  # pyright: ignore[reportUnknownMemberType]
                else:
                    raise

        except Exception as e:
            print("Play/Pause error:", e)

    def next_track(self) -> None:
        """Skip to the next track."""
        current = self.get_current_speaker()
        if not current:
            return
        try:
            current.next()
        except Exception as e:
            print("Next track error:", e)

    def prev_track(self) -> None:
        """Return to the previous track."""
        current = self.get_current_speaker()
        if not current:
            return
        try:
            current.previous()
        except Exception as e:
            print("Prev track error:", e)

    def set_volume(self, v: int) -> None:
        """Set the volume of the selected speaker."""
        current = self.get_current_speaker()
        if current:
            current.volume = v

    def toggle_mute(self) -> None:
        """Mute the selected speaker."""
        current = self.get_current_speaker()
        if not current:
            return

        try:
            muted = current.mute
            current.mute = not muted
        except Exception as e:
            print("Toggle mute error:", e)
