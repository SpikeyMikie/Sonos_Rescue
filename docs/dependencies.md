# Sonos Rescue Dependencies

## database/database.py

**external**
- `sqlite3`
- `threading`

## managers/artwork_manager.py

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

## managers/playback_controller.py

**external**
- `soco`
- `soco.exceptions`
- `typing`

## managers/playback_poller.py

**internal**
- `sonos_rescue.managers.artwork_manager`

**external**
- `PyQt6.QtCore`
- `collections.abc`
- `dataclasses`
- `soco`
- `typing`

## managers/speaker_manager.py

**external**
- `PyQt6.QtCore`
- `soco`
- `typing`

## services/local_music_server.py

**external**
- `errno`
- `functools`
- `http.server`
- `pathlib`
- `shutil`
- `threading`
- `typing`

## sonos_rescue.py

**internal**
- `ui.main_window`

**external**
- `PyQt6.QtWidgets`
- `sys`

## ui/artwork_panel.py

**internal**
- `sonos_rescue.database.database`
- `sonos_rescue.managers.artwork_manager`
- `widgets.rainbow_background`
- `widgets.rainbow_frame`
- `widgets.scaling_image_label`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

## ui/main_window.py

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

## ui/playlist_panel.py

**internal**
- `sonos_rescue.ui.widgets.rainbow_background`
- `sonos_rescue.ui.widgets.rainbow_frame`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtWidgets`

## ui/room_card.py

**internal**
- `sonos_rescue.managers.playback_controller`
- `transport_controls`
- `widgets.rainbow_background`
- `widgets.rainbow_frame`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`
- `soco`
- `typing`

## ui/rooms_panel.py

**internal**
- `sonos_rescue.managers.playback_controller`
- `sonos_rescue.managers.speaker_manager`
- `sonos_rescue.ui.room_card`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtWidgets`
- `soco`

## ui/transport_controls.py

**internal**
- `sonos_rescue.managers.playback_controller`
- `sonos_rescue.utils.resources`

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

## ui/widgets/rainbow_background.py

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

## ui/widgets/rainbow_frame.py

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

## ui/widgets/scaling_image_label.py

**external**
- `PyQt6.QtCore`
- `PyQt6.QtGui`
- `PyQt6.QtWidgets`

## utils/network.py

**external**
- `socket`

## utils/resources.py

**external**
- `importlib.abc`
- `importlib.resources`
