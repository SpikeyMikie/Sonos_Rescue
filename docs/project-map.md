# Sonos Rescue Project Map

## File Structure

```text
sonos_rescue
├── database
│   └── database.py
│       ├── doc: Database module for Sonos Rescue.
│       └── class ArtworkDatabase
│           ├── def __init__()
│           ├── def init_artwork_db()
│           ├── def get_artwork_data()
│           ├── def insert_artwork_data()
│           ├── def delete_artwork_data()
│           └── def close()
├── managers
│   ├── artwork_manager.py
│   │   ├── class ArtResult
│   │   ├── class ArtworkManager
│   │   │   ├── def __init__()
│   │   │   ├── def get_album_art_from_file()
│   │   │   ├── def resolve_and_fetch_art()
│   │   │   └── def set_album_art()
│   │   └── def resize_image()
│   ├── playback_controller.py
│   │   └── class PlaybackController
│   │       ├── def __init__()
│   │       ├── def play_pause()
│   │       ├── def next_track()
│   │       ├── def prev_track()
│   │       ├── def set_volume()
│   │       └── def toggle_mute()
│   ├── playback_poller.py
│   │   ├── doc: Playback poller for SoCo speakers.
│   │   ├── class NowPlayingUpdate
│   │   └── class PlaybackPoller
│   │       ├── def __init__()
│   │       ├── def poll_once()
│   │       ├── def start_polling()
│   │       └── def stop()
│   └── speaker_manager.py
│       └── class SpeakerManager
│           ├── def __init__()
│           ├── def discover_speakers()
│           └── def select_speaker()
├── resources
│   └── icons
├── services
│   └── local_music_server.py
│       ├── class LocalMusicServer
│       │   ├── def __init__()
│       │   ├── def start()
│       │   ├── def stop()
│       │   └── def _create_server()
│       ├── class QuietHTTPRequestHandler
│       │   ├── def copyfile()
│       │   └── def log_message()
│       └── class PortInUseError
├── ui
│   ├── widgets
│   │   ├── rainbow_background.py
│   │   │   └── class RainbowBackground
│   │   │       ├── def __init__()
│   │   │       ├── def set_alpha()
│   │   │       ├── def paintEvent()
│   │   │       └── def _create_gradient()
│   │   ├── rainbow_frame.py
│   │   │   └── class RainbowFrame
│   │   │       ├── def __init__()
│   │   │       ├── def set_border_width()
│   │   │       ├── def paintEvent()
│   │   │       └── def _create_gradient()
│   │   └── scaling_image_label.py
│   │       └── class ScalingImageLabel
│   │           ├── def __init__()
│   │           ├── def set_pixmap()
│   │           ├── def clear()
│   │           ├── def resizeEvent()
│   │           ├── def sizeHint()
│   │           ├── def minimumSizeHint()
│   │           └── def _update_scaled_pixmap()
│   ├── artwork_panel.py
│   │   └── class ArtworkPanel
│   │       ├── def __init__()
│   │       └── def display_artwork()
│   ├── main_window.py
│   │   ├── class MainWindow
│   │   │   ├── def __init__()
│   │   │   ├── def play_local_file()
│   │   │   ├── def display_local_artwork()
│   │   │   ├── def stream_local_file()
│   │   │   ├── def update_now_playing()
│   │   │   ├── def apply_now_playing_update()
│   │   │   ├── def display_selected_speaker()
│   │   │   ├── def add_to_queue()
│   │   │   └── def closeEvent()
│   │   └── class QueueItemProtocol
│   ├── playlist_panel.py
│   │   └── class PlaylistPanel
│   │       └── def __init__()
│   ├── room_card.py
│   │   └── class RoomCard
│   │       ├── def __init__()
│   │       ├── def set_selected()
│   │       ├── def mousePressEvent()
│   │       └── def eventFilter()
│   ├── rooms_panel.py
│   │   └── class RoomsPanel
│   │       ├── def __init__()
│   │       ├── def _build_header()
│   │       ├── def _build_scroll_area()
│   │       ├── def display_speakers()
│   │       └── def _room_selected()
│   └── transport_controls.py
│       └── class TransportControls
│           ├── def __init__()
│           ├── def create_icon_button()
│           ├── def update_play_pause_icon()
│           ├── def toggle_mute()
│           ├── def _on_play_pause_toggled()
│           ├── def _on_prev_clicked()
│           ├── def _on_next_clicked()
│           └── def _on_mute_toggled()
├── utils
│   ├── network.py
│   │   └── def get_local_ip()
│   └── resources.py
│       └── def resource_path()
└── sonos_rescue.py
    ├── doc: Main entry point for the Sonos Rescue application.
    └── def main()
```
