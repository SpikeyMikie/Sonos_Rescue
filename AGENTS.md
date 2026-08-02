---
name: Sonos Rescue Agent Instructions
description: |
    AI agent guidance for the Sonos Rescue project — a PyQt6-based desktop controller
    for Sonos speakers. Use when working on features, bug fixes, testing, or type checking
    in this codebase.
---

# Sonos Rescue Agent Instructions

## Project Overview

[Sonos Rescue](README.md) is a Python desktop application built with PyQt6 for controlling Sonos speakers on local networks. Unlike the official Sonos desktop software, this project prioritizes flexibility, local HTTP streaming, and advanced features.

**Key technologies:**

- **PyQt6** — Desktop GUI framework
- **SoCo** — Python library for Sonos device communication
- **Mutagen** — MP3 metadata and album artwork extraction
- **PIL (Pillow)** — Image processing
- **pytest** — Testing framework

**Current focus:** Remove all Pylance/Mypy type errors, modernize the GUI, and add music playback functionality.

## Architecture & Key Classes

### Core Application

- **`SonosApp`** ([sonos_rescue.py](sonos_rescue.py#L256)) — Main window; manages speaker discovery, playback controls, artwork caching, and the refresh loop

### Audio Streaming

- **`LocalMusicServer`** ([sonos_rescue.py](sonos_rescue.py#L127)) — HTTP server in daemon thread serving local music files to Sonos speakers. Handles port binding, folder validation, and graceful Sonos disconnections
- **`QuietHTTPRequestHandler`** — Suppresses logging and catches `BrokenPipeError` / `ConnectionResetError` when Sonos disconnects

### UI Components

- **`RoomCard`** ([sonos_rescue.py](sonos_rescue.py#L199)) — Card widget representing a discovered Sonos speaker

## Type Checking & Linting

**Current state:** Project uses **Pyright** (bundled in requirements.txt) with strict type checking enabled via `# pyright: ignore[reportUnknownMemberType]` comments where SoCo/PyQt6 lack type stubs.

**When making changes:**

1. Add type hints to new functions and variables wherever possible
2. Use `typing` module protocols for structural typing (see `QueueItemProtocol`, `APICProtocol` in [sonos_rescue.py](sonos_rescue.py))
3. If a Pyright error cannot be resolved due to missing type stubs, use inline `# pyright: ignore[...]` comments with a brief justification

**Goal:** Remove all Pyright warnings and errors.

## Testing

Tests are in [test.py](test.py) and use **pytest** with custom PyQt6 stubs (since PyQt6 imports break in test environments). The test file manually stubs PyQt6 classes to allow importing `sonos_rescue.py` without a full display.

**Running tests:**

```bash
pytest test.py -v
```

**Current test branch:** `fix/LocalMusicServer-error-handling` — Adding error handling for:

- Missing music folder → `FileNotFoundError`
- Port 8000 already in use → port fallback logic
- `start()` called twice → idempotency check (in progress)

## Dependencies & Setup

See [requirements.txt](requirements.txt) for exact versions. Key packages:

- `PyQt6==6.11.0` with `PyQt6-Qt6`, `PyQt6_sip`
- `soco==0.31.0` (Sonos communication)
- `mutagen==1.47.0` (MP3 metadata)
- `pillow==12.2.0` (image processing)
- `pyright==1.1.411` (type checking)
- `pytest==9.1.1` (testing)

## Common Patterns

### Threading

- Background work runs in daemon threads (e.g., `LocalMusicServer.start()`, `SonosApp.refresh_loop()`) to keep GUI responsive
- Use `threading.Thread(target=..., daemon=True).start()`

### Error Handling

- `LocalMusicServer` catches and gracefully handles `BrokenPipeError` when Sonos disconnects mid-stream
- Folder/port validation happens in `start()`, not `__init__()`

### GUI State Management

- `SonosApp.current` tracks the selected speaker
- Speaker list refreshed via background `refresh_loop()` thread
- Album artwork cached in `self.art_cache` to avoid repeated HTTP requests

## Workflow

1. **Feature/bug fixes:** Edit [sonos_rescue.py](sonos_rescue.py) or [test.py](test.py)
2. **Type checking:** Run `pyright sonos_rescue.py` and fix errors
3. **Testing:** Run `pytest test.py -v` to validate
4. **Type stubs:** For new SoCo/PyQt6 calls, use inline `# pyright: ignore[reportUnknownMemberType]` if necessary

## See Also

- **README:** [README.md](README.md) — Project vision, motivation, long-term goals
- **Project notes:** [project-notes.md](project-notes.md) — Active work, branch notes, TODO
- **License:** GNU v3 ([COPYING.txt](COPYING.txt))
