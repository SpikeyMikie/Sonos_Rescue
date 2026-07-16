# some new text to test git. 
# pyright: reportMissingImports=false
import sys
import threading
import time
from io import BytesIO
import soco  # type: ignore[import]
from PIL import Image  # type: ignore[import]
from urllib.request import Request, urlopen
from PyQt6.QtWidgets import ( 
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QSlider, QMessageBox, QFrame,
    QScrollArea, QInputDialog
) 
from PyQt6.QtCore import Qt  # type: ignore[import]
from PyQt6.QtGui import QPixmap  # type: ignore[import]
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import socket
from urllib.parse import quote
import shutil
from mutagen.mp3 import MP3  # type: ignore[import]
from mutagen.id3 import ID3  # type: ignore[import]


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
    def copyfile(self, source, outputfile):
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

    def log_message(self, format, *args):  # suppress logging
        """
        Disable default HTTP server request logging.

        The parent SimpleHTTPRequestHandler logs every request to the
        terminal. This is unnecessary for normal operation and would
        clutter the application's output.
        """
        return




class LocalMusicServer:
    """
    A lightweight HTTP server for serving local music files to Sonos devices.

    Sonos speakers cannot play files directly from the local filesystem, instead
    they require media to be accessible via an HTTP URL. 
    
    The server runs in a daemon thread, allowing it to operate alongside the
    main application without blocking the GUI.
    """
    def __init__(self, folder, port=8000):
        """
        Initialise the local music server.

        Args:
            folder (str): Directory containing the music files to serve.
            port (int, optional): TCP port on which the HTTP server listens.
                Defaults to 8000.
        """
        self.folder = folder
        self.port = port
        self.httpd = None

    def start(self):
        """
        Start the HTTP server in a background thread.

        The server changes the working directory to the configured music
        folder before serving files. Running the server in a daemon thread
        allows the GUI to remain responsive while music is streamed to
        Sonos devices.
        """

        # Serve files relative to the selected music directory.
        os.chdir(self.folder)

        handler = QuietHTTPRequestHandler
        self.httpd = HTTPServer(("0.0.0.0", self.port), handler)

        # Run the HTTP server in the background so it does not block the GUI.
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()

    def stop(self):
        """
        Stop the HTTP server if it is running.

        Shuts down the background server, preventing any new HTTP requests
        from being accepted.
        """
        if self.httpd:
            self.httpd.shutdown()


class RoomCard(QFrame):
    def __init__(self, speaker, on_select):
        super().__init__()
        self.speaker = speaker
        self.on_select = on_select

        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("padding:10px; margin:5px; border-radius:8px;")

        layout = QVBoxLayout()

        self.name = QLabel(speaker.player_name)
        self.status = QLabel("Idle")

        self.btn = QPushButton("Control")
        self.btn.clicked.connect(self.select)

        layout.addWidget(self.name)
        layout.addWidget(self.status)
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def select(self):
        self.on_select(self.speaker)


class SonosApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sonos Desktop Controller")
        self.setGeometry(100, 100, 1200, 700)
        self.speakers = []
        self.current = None
        self.album_pixmap = None
        self.art_cache = {}
        self.current_art_url = None
        self.build_ui()
        self.discover()
        self.running = True
        threading.Thread(target=self.refresh_loop, daemon=True).start()

    # ---------------- UI ---------------- #
    # Build the main UI layout
    def build_ui(self):
        root = QHBoxLayout()

        # LEFT: ROOMS PANEL
        self.rooms_container_widget = QWidget()
        self.rooms_layout = QVBoxLayout(self.rooms_container_widget)

        self.rooms_label = QLabel("Rooms")
        self.rooms_layout.addWidget(self.rooms_label)

        self.rooms_scroll = QScrollArea()
        self.rooms_scroll.setWidgetResizable(True)
        self.rooms_scroll.setWidget(self.rooms_container_widget)

        # CENTER: NOW PLAYING
        center_layout = QVBoxLayout()

        self.title = QLabel("No room selected")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:18px;")

        self.album = QLabel()
        self.album.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.track_info = QLabel("")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_layout.addWidget(self.title)
        center_layout.addWidget(self.album)
        center_layout.addWidget(self.track_info)

        controls = QHBoxLayout()

        self.play_btn = QPushButton("Play/Pause")
        self.play_btn.clicked.connect(self.play_pause)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_track)

        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(self.prev_track)

        controls.addWidget(self.play_btn)
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.next_btn)

        center_layout.addLayout(controls)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.valueChanged.connect(self.set_volume)

        center_layout.addWidget(QLabel("Volume"))
        center_layout.addWidget(self.volume)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # RIGHT: QUEUE
        right_layout = QVBoxLayout()

        self.queue = QListWidget()

        self.refresh_btn = QPushButton("Refresh Rooms")
        self.refresh_btn.clicked.connect(self.discover)

        right_layout.addWidget(QLabel("Queue"))
        right_layout.addWidget(self.queue)

        self.add_file_btn = QPushButton("Play Local File")
        self.add_file_btn.clicked.connect(self.play_local_file)
        right_layout.addWidget(self.add_file_btn)

        self.add_uri_btn = QPushButton("Add URL / URI to Queue")  # added
        self.add_uri_btn.clicked.connect(self.add_to_queue)  # added
        right_layout.addWidget(self.add_uri_btn)
        right_layout.addWidget(self.refresh_btn)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Assemble
        root.addWidget(self.rooms_scroll, 2)
        root.addWidget(center_widget, 3)
        root.addWidget(right_widget, 2)

        self.setLayout(root)

    # ---------------- DISCOVERY ---------------- #
    # Discover available Sonos speakers
    def discover(self):
        try:
            devices = soco.discover()
            self.speakers = list(devices) if devices else []

            # clear old cards
            for i in reversed(range(self.rooms_layout.count())):
                item = self.rooms_layout.itemAt(i)
                widget = item.widget() if item else None
                if widget:
                    widget.setParent(None)

            # add new cards
            for s in self.speakers:
                card = RoomCard(s, self.select_speaker)
                self.rooms_layout.addWidget(card)

            # adjust scroll area
            self.rooms_container_widget.adjustSize()
            self.rooms_scroll.update()
            self.rooms_container_widget.update()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # Select a speaker and update UI
    def select_speaker(self, speaker):
        self.current = speaker
        self.title.setText(speaker.player_name)

    # ---------------- CONTROLS ---------------- #

    def play_pause(self):
        if not self.current:
            return

        try:
            state = self.current.get_current_transport_info()[
                "current_transport_state"]

            if state == "PLAYING":
                self.current.pause()
                self.play_btn.setText("Pause")
            else:
                self.current.play()
                self.play_btn.setText("Play")

        except Exception as e:
            print("Play/Pause error:", e)

    def next_track(self):
        if self.current:
            self.current.next()

    def prev_track(self):
        if self.current:
            self.current.previous()

    def set_volume(self, v):
        if self.current:
            self.current.volume = v

    # ---------------- NOW PLAYING ---------------- #

    def update_now_playing(self):
        if not self.current:
            return
        try:
            track = self.current.get_current_track_info()
            title = track.get("title", "")
            artist = track.get("artist", "")
            album = track.get("album", "")
            self.track_info.setText(f"{title}\n{artist}\n{album}")
            art = track.get("album_art")

            if art != self.current_art_url:  # reset cache if art URL changes
                self.art_cache.pop(self.current_art_url,
                                   None)  # remove old cache
                self.current_art_url = None  # reset current art URL

            if art:
                self.load_art(art)

            # update queue (lightweight)
            q = self.current.get_queue()
            self.queue.clear()

            for item in q:
                self.queue.addItem(item.title)
        except:
            pass

    def play_local_file(self):
        if not self.current:
            return

        # moved import here to avoid unnecessary dependency if not using this feature
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Music File",
            "",
            "Audio Files (*.mp3 *.wav *.m4a)"
        )

        # ✅ CRITICAL: stop immediately if no file selected
        if not file_path:
            return

        try:
            filename = os.path.basename(file_path)

            # ✅ Extract album art FIRST (safe now)
            art_data = self.get_album_art_from_file(file_path)
            if art_data:
                pixmap = QPixmap()
                pixmap.loadFromData(art_data)
                self.album.setPixmap(pixmap)

            # Start/update server
            if not hasattr(self, "server"):
                self.server = LocalMusicServer(
                    os.path.dirname(file_path), 8000)
                self.server.start()
            else:
                self.server.folder = os.path.dirname(file_path)
                os.chdir(self.server.folder)

            # Build URL
            from urllib.parse import quote
            ip = self.get_local_ip()
            url = f"http://{ip}:8000/{quote(filename)}"

            print("Playing:", url)

            # Play on Sonos
            self.current.play_uri(url)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def get_album_art_from_file(self, file_path):
        try:
            audio = MP3(file_path, ID3=ID3)

            tags = audio.tags or {}

            for tag in tags.values():
                if getattr(tag, "FrameID", None) == "APIC":
                    if getattr(tag, "type", None) == 3:  # 3 = front cover
                        return tag.data

        except Exception as e:
            print("Album art error:", e)

        return None

    # Utility to get local IP address for server URL

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    # Load and display album art from URL
    def load_art(self, url):
        speaker = self.current
        if not speaker:
            return

        try:
            if not url.startswith("http"):
                url = f"http://{speaker.ip_address}:1400{url}"

            # If same URL as last time do nothing
            if url == self.current_art_url:
                return

            self.current_art_url = url

            # If cached use it
            if url in self.art_cache:
                self.album.setPixmap(self.art_cache[url])
                return

            # Otherwise fetch it
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=3) as response:
                data = response.read()

            img = Image.open(BytesIO(data)).resize((300, 300))

            data = BytesIO()
            img.save(data, format="PNG")

            pixmap = QPixmap()
            pixmap.loadFromData(data.getvalue())

            # Store in cache
            self.art_cache[url] = pixmap
            MAX_CACHE = 20

            if len(self.art_cache) > MAX_CACHE:
                self.art_cache.pop(next(iter(self.art_cache)))

            self.album.setPixmap(pixmap)

        except Exception as e:
            print("Album load error:", e)

    # ---------------- LOOP ---------------- #

    def refresh_loop(self):
        while self.running:
            try:
                self.update_now_playing()
            except:
                pass
            time.sleep(2)

    def add_to_queue(self):
        if not self.current:
            QMessageBox.warning(self, "No speaker", "Select a room first")
            return

        url, ok = QInputDialog.getText(
            self,
            "Add URL / URI to Queue",
            "Enter stream URL or Sonos-supported URI:"
        )

        if not ok or not url:
            return

        try:
            # OPTION 1: add to queue
            self.current.add_to_queue(url)

            # refresh queue view immediately
            self.update_now_playing()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SonosApp()
    window.show()
    sys.exit(app.exec())
