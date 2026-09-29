# Sonos Rescue Project Map

## File Structure

```text
sonos_rescue
├── database
│   └── database.py
│       ├── doc: Database module for Sonos Rescue.
│       └── class ArtworkDatabase
│           ├── doc: Simple SQLite cache for artwork bytes.
│           └── methods
│               ├── dunder: def __init__(self, db_path: str = ':memory:') -> None
│               ├── public: def init_artwork_db(self) -> None
│               ├── public: def get_artwork_data(self, url: str) -> bytes | None
│               │   └── doc: Retrieve artwork data for a given URL.
│               ├── public: def insert_artwork_data(self, url: str, data: bytes) -> None
│               ├── public: def delete_artwork_data(self, url: str) -> None
│               └── public: def close(self) -> None
├── managers
│   ├── artwork_manager.py
│   │   ├── class ArtResult
│   │   │   ├── doc: Immutable result of an artwork retrieval operation.
│   │   │   └── decorators: @dataclass(frozen=True)
│   │   ├── class ArtworkManager
│   │   │   ├── doc: Manages album artwork retrieval, caching, and display for Sonos devices.
│   │   │   └── methods
│   │   │       ├── dunder: def __init__(self, database: ArtworkDatabase) -> None
│   │   │       ├── public: def get_album_art_from_file(self, file_path: str | Path) -> bytes | None
│   │   │       │   └── doc: Extract any embedded front-cover artwork from an MP3 file. Returns: bytes | None: The embedded image data, or None if no artwor...
│   │   │       ├── public: def resolve_and_fetch_art(self, url: str, speaker: SoCo) -> ArtResult
│   │   │       │   └── doc: Resolve an artwork URL and fetch its bytes. Safe to call from a worker thread: touches only plain data and the thread-safe artw...
│   │   │       └── public: def set_album_art(self, album_label: QLabel, pixmap: QPixmap) -> QLabel
│   │   │           └── doc: Set the album art on the given QLabel. The image is expected to already be square-cropped to 500x500 before it reaches the labe...
│   │   └── public: def resize_image(image: PILImage, size: tuple[int, int]) -> PILImage
│   │       └── doc: Resize a Pillow image to the requested dimensions. Kept separate from the main album-loading function to isolate image manipula...
│   ├── playback_controller.py
│   │   └── class PlaybackController
│   │       ├── doc: Handles playback control for the selected Sonos speaker. This class provides methods to play, pause, skip tracks, and adjust vo...
│   │       └── methods
│   │           ├── dunder: def __init__(self, get_current_speaker: Callable[[], SoCo | None]) -> None
│   │           │   └── doc: Initialise the playback controller. Args: get_current_speaker: A callable that returns the currently selected SoCo speaker, or ...
│   │           ├── public: def play_pause(self) -> None
│   │           │   └── doc: Toggle playback for the selected speaker.
│   │           ├── public: def next_track(self) -> None
│   │           │   └── doc: Skip to the next track.
│   │           ├── public: def prev_track(self) -> None
│   │           │   └── doc: Return to the previous track.
│   │           ├── public: def set_volume(self, v: int) -> None
│   │           │   └── doc: Set the volume of the selected speaker.
│   │           └── public: def toggle_mute(self) -> None
│   │               └── doc: Mute the selected speaker.
│   ├── playback_poller.py
│   │   ├── doc: Playback poller for SoCo speakers.
│   │   ├── class NowPlayingUpdate
│   │   │   ├── doc: Immutable playback snapshot passed from the refresh worker to Qt.
│   │   │   └── decorators: @dataclass(frozen=True)
│   │   └── class PlaybackPoller
│   │       ├── doc: Polls the current playback state of a SoCo speaker and emits updates.
│   │       ├── bases: QObject
│   │       └── methods
│   │           ├── dunder: def __init__(self, get_current_speaker: Callable[[], SoCo | None], artwork_manager: ArtworkManager) -> None
│   │           ├── public: def poll_once(self) -> None
│   │           │   ├── decorators: @pyqtSlot()
│   │           │   └── doc: Poll the current speaker once and emit a NowPlayingUpdate signal.
│   │           ├── public: def start_polling(self) -> None
│   │           │   ├── decorators: @pyqtSlot()
│   │           │   └── doc: Start periodic polling on the worker thread event loop.
│   │           └── public: def stop(self) -> None
│   │               ├── decorators: @pyqtSlot()
│   │               └── doc: Stop periodic polling.
│   └── speaker_manager.py
│       └── class SpeakerManager
│           ├── doc: Manages the discovery and selection of Sonos speakers. This class encapsulates the logic for discovering available Sonos device...
│           ├── bases: QObject
│           └── methods
│               ├── dunder: def __init__(self) -> None
│               ├── public: def discover_speakers(self) -> None
│               │   └── doc: Discover Sonos speakers on the local network. Clears any existing room cards and rebuilds the speaker list to reflect the curre...
│               └── public: def select_speaker(self, speaker: SoCo) -> None
│                   └── doc: Make the selected speaker the active playback device. Args: speaker: The SoCo speaker instance selected by the user.
├── resources
│   └── icons
├── services
│   └── local_music_server.py
│       ├── class LocalMusicServer
│       │   ├── doc: A lightweight HTTP server for serving local music files to Sonos devices. Sonos speakers cannot play files directly from the lo...
│       │   └── methods
│       │       ├── dunder: def __init__(self, folder: Path, port: int | None = None) -> None
│       │       │   └── doc: Initialise the local music server. Args: folder: Directory containing the music files to serve. port (optional): TCP port on wh...
│       │       ├── public: def start(self) -> None
│       │       │   └── doc: Start the HTTP server in a background thread. The server serves files from the configured music folder without changing the pro...
│       │       ├── public: def stop(self) -> None
│       │       │   └── doc: Stop the HTTP server if it is running. Shuts down the background server, preventing any new HTTP requests from being accepted.
│       │       └── private: def _create_server(self, handler: HandlerFactory) -> HTTPServer
│       │           └── doc: Create an HTTP server. Attempts to bind to the configured port and, if it is already in use, tries successive ports until one i...
│       ├── class QuietHTTPRequestHandler
│       │   ├── doc: Custom HTTP request handler for serving local music files to Sonos devices. Extends Python's built-in SimpleHTTPRequestHandler ...
│       │   ├── bases: SimpleHTTPRequestHandler
│       │   └── methods
│       │       ├── public: def copyfile(self, source: BinaryIO, outputfile: BinaryIO) -> None
│       │       │   └── doc: Copy file data from the requested resource to the HTTP response. Overrides the parent class method to gracefully handle cases w...
│       │       └── public: def log_message(self, format: str, *args: object) -> None
│       │           └── doc: Disable default HTTP server request logging. The parent SimpleHTTPRequestHandler logs every request to the terminal. This is un...
│       └── class PortInUseError
│           ├── doc: Raised when the HTTP server port is already in use.
│           └── bases: Exception
├── ui
│   ├── widgets
│   │   ├── rainbow_background.py
│   │   │   └── class RainbowBackground
│   │   │       ├── doc: A widget that fills its whole area with a translucent rainbow gradient. parameters: - radius: the corner radius of the backgrou...
│   │   │       ├── bases: QWidget
│   │   │       └── methods
│   │   │           ├── dunder: def __init__(self, parent: QWidget | None = None, radius: int = 12, alpha: int = 150)
│   │   │           ├── public: def set_alpha(self, alpha: int) -> None
│   │   │           │   └── doc: Update the background translucency and repaint.
│   │   │           ├── public: def paintEvent(self, a0: QPaintEvent | None) -> None
│   │   │           └── private: def _create_gradient(self, rect: QRectF, alpha: int = 255) -> QConicalGradient
│   │   │               └── doc: Create the rainbow gradient used by the background.
│   │   ├── rainbow_frame.py
│   │   │   └── class RainbowFrame
│   │   │       ├── doc: A QFrame with a soft glowing rainbow border.
│   │   │       ├── bases: QFrame
│   │   │       └── methods
│   │   │           ├── dunder: def __init__(self, parent: QFrame | None = None, border_width: int = 30, glow_width: int = 10, radius: int = 12) -> None
│   │   │           ├── public: def set_border_width(self, border_width: int) -> None
│   │   │           ├── public: def paintEvent(self, a0: QPaintEvent | None) -> None
│   │   │           └── private: def _create_gradient(self, rect: QRectF, alpha: int = 255) -> QConicalGradient
│   │   │               └── doc: Create the rainbow gradient used by the border.
│   │   └── scaling_image_label.py
│   │       └── class ScalingImageLabel
│   │           ├── doc: A QLabel that rescales its pixmap (keeping aspect ratio) to fill its current size.
│   │           ├── bases: QLabel
│   │           └── methods
│   │               ├── dunder: def __init__(self, pixmap: QPixmap, parent: QWidget | None = None)
│   │               ├── public: def set_pixmap(self, pixmap: QPixmap) -> None
│   │               │   └── doc: Store the source pixmap and display it scaled to the current size.
│   │               ├── public: def clear(self) -> None
│   │               │   └── doc: Clear both the displayed image and its source pixmap.
│   │               ├── public: def resizeEvent(self, a0: QResizeEvent | None) -> None
│   │               ├── public: def sizeHint(self) -> QSize
│   │               ├── public: def minimumSizeHint(self) -> QSize
│   │               └── private: def _update_scaled_pixmap(self) -> None
│   ├── artwork_panel.py
│   │   └── class ArtworkPanel
│   │       ├── bases: QWidget
│   │       └── methods
│   │           ├── dunder: def __init__(self)
│   │           └── public: def display_artwork(self, pixmap: QPixmap | None) -> None
│   │               └── doc: Update the displayed artwork, or clear it if pixmap is None.
│   ├── main_window.py
│   │   ├── class MainWindow
│   │   │   ├── bases: QMainWindow
│   │   │   └── methods
│   │   │       ├── dunder: def __init__(self, parent: QMainWindow | None = None)
│   │   │       ├── public: def play_local_file(self) -> None
│   │   │       │   └── doc: Prompt for a local music file, then display its artwork and stream it.
│   │   │       ├── public: def display_local_artwork(self, file_path: Path) -> None
│   │   │       │   └── doc: Extract and display any embedded album artwork for a local file.
│   │   │       ├── public: def stream_local_file(self, file_path: Path) -> None
│   │   │       │   └── doc: Serve a local file over HTTP and instruct the selected speaker to play it.
│   │   │       ├── public: def update_now_playing(self) -> None
│   │   │       │   └── doc: Trigger an immediate poll of the selected speaker.
│   │   │       ├── public: def apply_now_playing_update(self, update: NowPlayingUpdate) -> None
│   │   │       │   └── doc: Apply a playback snapshot on the Qt main thread.
│   │   │       ├── public: def display_selected_speaker(self, speaker: SoCo) -> None
│   │   │       │   └── doc: Update the GUI to reflect the currently selected Sonos speaker.
│   │   │       ├── public: def add_to_queue(self) -> None
│   │   │       │   └── doc: Add a network stream or Sonos-compatible URI to the playback queue. Prompts the user for a URI and updates the displayed queue ...
│   │   │       └── public: def closeEvent(self, a0: QCloseEvent | None) -> None
│   │   │           └── doc: Handle the window close event by stopping the playback poller.
│   │   └── class QueueItemProtocol
│   │       ├── doc: Defines the minimum interface required for Sonos queue items. SoCo queue objects contain many attributes, but this application ...
│   │       └── bases: Protocol
│   ├── playlist_panel.py
│   │   └── class PlaylistPanel
│   │       ├── bases: QWidget
│   │       └── methods
│   │           └── dunder: def __init__(self)
│   ├── room_card.py
│   │   └── class RoomCard
│   │       ├── bases: QWidget
│   │       └── methods
│   │           ├── dunder: def __init__(self, room_name: str, speaker: SoCo, on_select: Callable[[SoCo], None], playback_controller: PlaybackController)
│   │           ├── public: def set_selected(self, selected: bool) -> None
│   │           ├── public: def mousePressEvent(self, a0: QMouseEvent | None) -> None
│   │           └── public: def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool
│   ├── rooms_panel.py
│   │   └── class RoomsPanel
│   │       ├── bases: QWidget
│   │       └── methods
│   │           ├── dunder: def __init__(self, speaker_manager: SpeakerManager, playback_controller: PlaybackController, parent: QWidget | None = None)
│   │           ├── private: def _build_header(self) -> None
│   │           ├── private: def _build_scroll_area(self) -> None
│   │           ├── public: def display_speakers(self, speakers: list[SoCo]) -> None
│   │           │   └── doc: Rebuild the room cards from the discovered speakers list.
│   │           └── private: def _room_selected(self, room_card: RoomCard) -> None
│   └── transport_controls.py
│       └── class TransportControls
│           ├── bases: QWidget
│           └── methods
│               ├── dunder: def __init__(self, playback_controller: PlaybackController)
│               ├── public: def create_icon_button(self, icon_file: str) -> QPushButton
│               ├── public: def update_play_pause_icon(self, playing: bool) -> None
│               ├── public: def toggle_mute(self, muted: bool) -> None
│               ├── private: def _on_play_pause_toggled(self, _checked: bool) -> None
│               ├── private: def _on_prev_clicked(self, _checked: bool) -> None
│               ├── private: def _on_next_clicked(self, _checked: bool) -> None
│               └── private: def _on_mute_toggled(self, _checked: bool) -> None
├── utils
│   ├── network.py
│   │   └── public: def get_local_ip() -> str
│   │       └── doc: Determine the local IPv4 address of this machine. A UDP socket is used only to discover the preferred network interface. No dat...
│   └── resources.py
│       └── public: def resource_path(filename: str) -> Traversable
└── sonos_rescue.py
    ├── doc: Main entry point for the Sonos Rescue application.
    └── public: def main() -> None
        └── doc: Entry point for the Sonos Rescue application. Create the QApplication instance, initialise the main window, and start the event...
```
