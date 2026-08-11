import errno
import shutil
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import BinaryIO, Callable, TypeAlias
from pathlib import Path


class LocalMusicServer:
    """
    A lightweight HTTP server for serving local music files to Sonos devices.

    Sonos speakers cannot play files directly from the local filesystem, instead
    they require media to be accessible via an HTTP URL.

    The server runs in a daemon thread, allowing it to operate alongside the
    main application without blocking the GUI.
    """

    DEFAULT_PORT: int = 8000
    MAX_PORT_ATTEMPTS: int = 50

    def __init__(self, folder: Path, port: int | None = None) -> None:
        """
        Initialise the local music server.

        Args:
        folder:
            Directory containing the music files to serve.
        port (optional):
            TCP port on which the HTTP server listens.
            Defaults to 8000.
        """
        self.folder: Path = folder
        self.port: int = port if port is not None else self.DEFAULT_PORT
        self.httpd: HTTPServer | None = None

    def start(self) -> None:
        """
        Start the HTTP server in a background thread.

        The server changes the working directory to the configured music
        folder before serving files. Running the server in a daemon thread
        allows the GUI to remain responsive while music is streamed to
        Sonos devices.
        """
        if self.httpd is not None:
            raise RuntimeError("LocalMusicServer is already running")

        if not self.folder.is_dir():
            raise FileNotFoundError(
                f"Music folder does not exist or is invalid: {self.folder}"
            )

        # Serve files relative to the selected music directory.

        handler = partial(QuietHTTPRequestHandler, directory=str(self.folder))

        self.httpd = self._create_server(handler)

        # Run the HTTP server in the background so it does not block the GUI.
        thread = threading.Thread(
            target=self.httpd.serve_forever,
            daemon=True,
        )
        thread.start()

    def stop(self) -> None:
        """
        Stop the HTTP server if it is running.

        Shuts down the background server, preventing any new HTTP requests
        from being accepted.
        """
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

    # type alias for a callable that returns a SimpleHTTPRequestHandler instance.
    HandlerFactory: TypeAlias = Callable[..., SimpleHTTPRequestHandler]

    def _create_server(self, handler: HandlerFactory) -> HTTPServer:
        """
        Create an HTTP server.

        Attempts to bind to the configured port and, if it is already
        in use, tries successive ports until one is available.
        """

        start_port = self.port
        for port in range(self.port, self.port + self.MAX_PORT_ATTEMPTS):
            try:
                server = HTTPServer(
                    ("0.0.0.0", port),
                    handler,
                )
                self.port = port
                return server
            except OSError as ose:
                if ose.errno == errno.EADDRINUSE:
                    continue
                raise
        raise PortInUseError(
            f"Could not find a free port between "
            f"{start_port} and "
            f"{start_port + self.MAX_PORT_ATTEMPTS - 1}."
        )


# custom handler to suppress logging and handle broken connections gracefully
class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for serving local music files to Sonos devices.

    Extends Python's built-in SimpleHTTPRequestHandler to:
    - Prevent server crashes when Sonos disconnects unexpectedly.
    - Suppress default HTTP request logging to keep the console output clean.

    This handler is used by the local HTTP server to make locally stored
    music files accessible through HTTP URLs that Sonos can play.
    """

    def copyfile(  # type: ignore[override]
        self, source: BinaryIO, outputfile: BinaryIO
    ) -> None:
        """
        Copy file data from the requested resource to the HTTP response.

        Overrides the parent class method to gracefully handle cases where
        the Sonos device disconnects before the file transfer completes.

        Args:
            source:
                The file object containing the requested file data.
            outputfile:
                The file object used to send data back to the client.

        Returns:
            None
        """

        try:
            shutil.copyfileobj(source, outputfile)

        # Sonos may stop requesting data before the transfer finishes,
        # causing the client connection to close unexpectedly.
        except (BrokenPipeError, ConnectionResetError):
            pass

    # suppress logging
    def log_message(self, format: str, *args: object) -> None:
        """
        Disable default HTTP server request logging.

        The parent SimpleHTTPRequestHandler logs every request to the
        terminal. This is unnecessary for normal operation and would
        clutter the application's output.
        """

        return None


class PortInUseError(Exception):
    """Raised when the HTTP server port is already in use."""

    pass
