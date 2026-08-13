import io
import os
import socket
from typing import Any, cast
from pathlib import Path
import pytest
import errno
import sonos_rescue.services.local_music_server as local_mod
from sonos_rescue.services.local_music_server import (
    LocalMusicServer,
    PortInUseError,
    QuietHTTPRequestHandler,
)


def test_quiet_copyfile_handles_errors():
    """Verify QuietHTTPRequestHandler.copyfile swallows broken-pipe and
    connection-reset errors without raising so the server stays stable.

    This test constructs a handler instance and passes fake output objects
    that raise BrokenPipeError and ConnectionResetError from their
    write methods. The thread should not crash and no exception should
    propagate out of copyfile.
    """

    handler = QuietHTTPRequestHandler.__new__(QuietHTTPRequestHandler)

    class BadOutput(io.BytesIO):
        def write(self, b: Any, /) -> int:
            raise BrokenPipeError()

    # should not raise
    QuietHTTPRequestHandler.copyfile(
        handler,
        io.BytesIO(b"abc"),
        cast(Any, BadOutput()),
    )

    class BadOutput2(io.BytesIO):
        def write(self, b: Any, /) -> int:
            raise ConnectionResetError()

    QuietHTTPRequestHandler.copyfile(
        handler,
        io.BytesIO(b"abc"),
        cast(Any, BadOutput2()),
    )


def test_local_music_server_start_stop(tmp_path: Path):
    """Start and stop the LocalMusicServer.

    Ensures `start()` initialises `httpd` and `stop()` shuts down the server
    without error. Port 0 allows the operating system to select an available port.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """

    server = LocalMusicServer(tmp_path, port=0)
    server.start()
    try:
        assert server.httpd is not None
    finally:
        server.stop()


def test_local_music_server_start_preserves_cwd(tmp_path: Path):
    """Starting the local music server should not change the process cwd."""
    server = LocalMusicServer(tmp_path, port=0)
    before = os.getcwd()
    server.start()
    try:
        assert os.getcwd() == before
    finally:
        server.stop()
        assert os.getcwd() == before


def test_local_music_server_preferred_port_available(tmp_path: Path):
    """Start a LocalMusicServer with a preferred port when it is available.

    Args:
        tmp_path (Path): temporary directory for the server's served folder
    """
    server = LocalMusicServer(folder=tmp_path, port=8123)
    server.start()
    try:
        assert server.port == 8123, "expected preferred port to be used"
    finally:
        server.stop()


def test_local_music_server_preferred_port_occupied(tmp_path: Path):
    """Use the next available port when the preferred port is occupied.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 8123))

    try:
        server = LocalMusicServer(folder=tmp_path, port=8123)
        server.start()
        try:
            assert server.port == 8124
        finally:
            server.stop()
    finally:
        sock.close()


def test_local_music_server_start_if_already_running_raises_error(tmp_path: Path):
    """Raise RuntimeError when starting an already running server.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """

    server = LocalMusicServer(folder=tmp_path, port=0)

    server.start()

    try:
        with pytest.raises(RuntimeError, match="already running"):
            server.start()
    finally:
        server.stop()


def test_local_music_server_all_ports_occupied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Raise PortInUseError when all preferred ports are occupied.

    Args:
        tmp_path (Path): Temporary directory used as the server's served folder.
    """
    server = LocalMusicServer(folder=tmp_path, port=8123)
    monkeypatch.setattr(local_mod, "HTTPServer", fake_http_server)

    try:
        with pytest.raises(PortInUseError):
            server.start()
    finally:
        server.stop()


class fake_http_server:
    """Simulate an OSError caused by an occupied HTTP server port."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise OSError(errno.EADDRINUSE, "Address already in use")


def test_local_music_server_rejects_invalid_folder(tmp_path: Path):
    """Raise FileNotFoundError when the server folder does not exist.

    This exercises the defensive check directly, without needing the file
    picker to produce an invalid path.

    Args:
        tmp_path (Path): Temporary directory used to create the missing folder.
    """

    missing_folder = tmp_path / "missing"
    server = LocalMusicServer(folder=missing_folder, port=0)

    with pytest.raises(FileNotFoundError, match=str(missing_folder)):
        server.start()
