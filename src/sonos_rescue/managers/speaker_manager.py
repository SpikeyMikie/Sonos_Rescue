import soco  # type: ignore[import-untyped]
from typing import cast
from PyQt6.QtCore import QObject, pyqtSignal
from soco import SoCo  # type: ignore[import-untyped]


class SpeakerManager(QObject):
    """
    Manages the discovery and selection of Sonos speakers.

    This class encapsulates the logic for discovering available Sonos devices
    on the local network, maintaining a list of discovered speakers, and
    allowing the user to select a speaker for control.
    """

    speakers_discovered = pyqtSignal(list)
    speaker_selected = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.speakers: list[SoCo] = []
        self.current: SoCo | None = None

    def discover_speakers(self) -> None:
        """
        Discover Sonos speakers on the local network.

        Clears any existing room cards and rebuilds the speaker list to
        reflect the currently available devices.
        """
        try:
            devices = cast(
                set[SoCo] | None,
                soco.discover(),  # pyright: ignore[reportUnknownMemberType]
            )
            self.speakers = list(devices) if devices else []
            self.speakers_discovered.emit(self.speakers)

        # Note: changed exception back to a simple print for now, will decide  if signal needed later.
        # Reason: QMessageBox.critical() expects a QWidget as its parent, whereas self is now a
        # SpeakerManager, which is a QObject, not a QWidget.
        except Exception as e:
            print("Speaker discovery error:", e)

    def select_speaker(self, speaker: SoCo) -> None:
        """
        Make the selected speaker the active playback device.

        Args:
            speaker: The SoCo speaker instance selected by the user.
        """
        self.current = speaker
        self.speaker_selected.emit(speaker)
