# Sonos Rescue Dependencies

## Import Dependencies

### `sonos_rescue.database.database`

**external**
- `sqlite3`
- `threading`

### `sonos_rescue.managers.artwork_manager`

**internal**
- `sonos_rescue.database.database`

**external**
- `PIL`
- `PIL.Image`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`
- `__future__`
- `dataclasses`
- `io`
- `mutagen.id3`
- `mutagen.id3._frames`
- `mutagen.mp3`
- `pathlib`
- `soco`
- `typing`
- `urllib.request`

### `sonos_rescue.managers.playback_controller`

**external**
- `soco`
- `soco.exceptions`
- `typing`

### `sonos_rescue.managers.playback_poller`

**internal**
- `sonos_rescue.managers.artwork_manager`

**external**
- `PyQt6.QtCore`
- `collections.abc`
- `dataclasses`
- `soco`
- `typing`

### `sonos_rescue.managers.speaker_manager`

**external**
- `PyQt6.QtCore`
- `soco`
- `typing`

### `sonos_rescue.services.local_music_server`

**external**
- `errno`
- `functools`
- `http.server`
- `pathlib`
- `shutil`
- `threading`
- `typing`

### `sonos_rescue.sonos_rescue`

**internal**
- `sonos_rescue.ui.main_window`

**external**
- `PyQt6.QtWidgets`
- `sys`

### `sonos_rescue.ui.artwork_panel`

**internal**
- `sonos_rescue.database.database`
- `sonos_rescue.managers.artwork_manager`
- `sonos_rescue.ui.widgets.rainbow_background`
- `sonos_rescue.ui.widgets.rainbow_frame`
- `sonos_rescue.ui.widgets.scaling_image_label`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

### `sonos_rescue.ui.main_window`

**internal**
- `sonos_rescue.database.database`
- `sonos_rescue.managers.artwork_manager`
- `sonos_rescue.managers.playback_controller`
- `sonos_rescue.managers.playback_poller`
- `sonos_rescue.managers.speaker_manager`
- `sonos_rescue.services.local_music_server`
- `sonos_rescue.ui.artwork_panel`
- `sonos_rescue.ui.playlist_panel`
- `sonos_rescue.ui.rooms_panel`
- `sonos_rescue.utils.network`
- `sonos_rescue.utils.resources`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`
- `pathlib`
- `soco`
- `typing`
- `urllib.parse`

### `sonos_rescue.ui.playlist_panel`

**internal**
- `sonos_rescue.ui.widgets.rainbow_background`
- `sonos_rescue.ui.widgets.rainbow_frame`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtWidgets`

### `sonos_rescue.ui.room_card`

**internal**
- `sonos_rescue.managers.playback_controller`
- `sonos_rescue.ui.transport_controls`
- `sonos_rescue.ui.widgets.rainbow_background`
- `sonos_rescue.ui.widgets.rainbow_frame`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`
- `soco`
- `typing`

### `sonos_rescue.ui.rooms_panel`

**internal**
- `sonos_rescue.managers.playback_controller`
- `sonos_rescue.managers.speaker_manager`
- `sonos_rescue.ui.room_card`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtWidgets`
- `soco`

### `sonos_rescue.ui.transport_controls`

**internal**
- `sonos_rescue.managers.playback_controller`
- `sonos_rescue.utils.resources`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

### `sonos_rescue.ui.widgets.rainbow_background`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

### `sonos_rescue.ui.widgets.rainbow_frame`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

### `sonos_rescue.ui.widgets.scaling_image_label`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

### `sonos_rescue.utils.network`

**external**
- `socket`

### `sonos_rescue.utils.resources`

**external**
- `importlib.abc`
- `importlib.resources`
