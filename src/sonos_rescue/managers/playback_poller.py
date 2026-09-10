"""Playback poller for SoCo speakers."""

from dataclasses import dataclass
from collections.abc import Callable, Iterable
from typing import Any, cast
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from soco import SoCo  # type: ignore[import-untyped]
from sonos_rescue.managers.artwork_manager import ArtResult, ArtworkManager


@dataclass(frozen=True)
class NowPlayingUpdate:
    """Immutable playback snapshot passed from the refresh worker to Qt."""

    title: str
    artist: str
    album: str
    queue_titles: tuple[str, ...]
    art_result: ArtResult | None


class PlaybackPoller(QObject):
    """Polls the current playback state of a SoCo speaker and emits updates."""

    now_playing_updated = pyqtSignal(object)

    def __init__(
        self,
        get_current_speaker: Callable[[], SoCo | None],
        artwork_manager: ArtworkManager,
    ) -> None:
        super().__init__()
        self.get_current_speaker = get_current_speaker
        self.artwork_manager = artwork_manager
        self._timer: QTimer | None = None

    @pyqtSlot()
    def poll_once(self) -> None:
        """Poll the current speaker once and emit a NowPlayingUpdate signal."""
        current = self.get_current_speaker()
        if not current:
            return

        try:
            track_info = cast(dict[str, Any], current.get_current_track_info())
            title = str(track_info.get("title", ""))
            artist = str(track_info.get("artist", ""))
            album = str(track_info.get("album", ""))

            queue_raw = current.get_queue()
            queue_titles: list[str] = []
            if queue_raw:
                for item in cast(Iterable[Any], queue_raw):
                    if isinstance(item, dict):
                        item_dict = cast(dict[str, Any], item)
                        queue_titles.append(str(item_dict.get("title", "")))
                    else:
                        queue_titles.append(str(getattr(item, "title", "")))

            art_url = track_info.get("album_art")
            art_result: ArtResult | None = None
            if art_url and isinstance(art_url, str):
                art_result = self.artwork_manager.resolve_and_fetch_art(
                    art_url, current
                )

            update = NowPlayingUpdate(
                title=title,
                artist=artist,
                album=album,
                queue_titles=tuple(queue_titles),
                art_result=art_result,
            )
            self.now_playing_updated.emit(update)
        except Exception as e:
            print("Poll once error:", e)

    @pyqtSlot()
    def start_polling(self) -> None:
        """Start periodic polling on the worker thread event loop."""
        if self._timer is not None and self._timer.isActive():
            return
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setInterval(2000)
            self._timer.timeout.connect(  # pyright: ignore[reportUnknownMemberType]
                self.poll_once
            )
        self._timer.start()  # pyright: ignore[reportUnknownMemberType]
        self.poll_once()

    @pyqtSlot()
    def stop(self) -> None:
        """Stop periodic polling."""
        if self._timer is not None:
            self._timer.stop()  # pyright: ignore[reportUnknownMemberType]
