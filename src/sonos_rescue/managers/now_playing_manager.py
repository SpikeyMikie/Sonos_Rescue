"""Now Playing Manager: Defines the NowPlayingUpdate dataclass for immutable playback state snapshots."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NowPlayingUpdate:
    """Immutable snapshot of playback state, produced off the main thread."""

    title: str
    artist: str
    album: str
    queue_titles: list[str]
    art_url: str | None
    art_bytes: bytes | None
