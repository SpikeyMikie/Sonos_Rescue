from __future__ import annotations
from io import BytesIO
from pathlib import Path
from typing import cast
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC as APICProtocol
from PIL.Image import Image as PILImage
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from soco import SoCo  # type: ignore[import-untyped]
from urllib.request import Request, urlopen

from sonos_rescue.database.database import ArtworkDatabase


class ArtworkManager:
    """
    Manages album artwork retrieval, caching, and display for Sonos devices.
    """

    def __init__(self, database: ArtworkDatabase) -> None:
        self.database = database
        self.art_cache: dict[str, QPixmap] = {}
        self.current_art_url: str | None = None
        self.displayed_art_url: str | None = None

    def get_album_art_from_file(self, file_path: str | Path) -> bytes | None:
        """
        Extract any embedded front-cover artwork from an MP3 file.

        Returns:
            bytes | None: The embedded image data, or None if no artwork is
            available.
        """
        file_path = Path(file_path)

        try:
            audio = MP3(file_path, ID3=ID3)

            tags = cast(
                dict[object, APICProtocol] | None,
                audio.tags,  # pyright: ignore[reportUnknownMemberType]
            )

            if tags is None:
                return None

            for tag in tags.values():
                if getattr(tag, "FrameID", None) == "APIC":
                    if getattr(tag, "type", None) == 3:  # 3 = front cover
                        return getattr(tag, "data", None)

        except Exception as e:
            print("Album art error:", e)

        return None

    # Load and display album art from URL
    def load_art(self, url: str, speaker: SoCo, album_label: QLabel) -> None:
        """
        Load and display album art from a given URL.
        Args:
            url (str): The URL of the album artwork.
            speaker (SoCo): The Sonos speaker instance.
            album_label (QLabel): The QLabel widget to display the artwork.
        """
        try:
            if not url or url == "None":
                return

            if not url.startswith("http"):
                speaker_ip = cast(str, speaker.ip_address)
                url = f"http://{speaker_ip}:1400{url}"

            if not url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                return

            self.current_art_url = url

            if url == self.displayed_art_url:
                return

            # check if the artwork is already cached in memory
            if url in self.art_cache:
                album_label.setPixmap(self.art_cache[url])
                self.displayed_art_url = url
                return

            # if the artwork is already cached in the database, load it from there
            cached_bytes = self.database.get_artwork_data(url)
            if cached_bytes is not None:
                cached_pixmap = QPixmap()
                cached_pixmap.loadFromData(cached_bytes)
                self.art_cache[url] = cached_pixmap
                album_label.setPixmap(cached_pixmap)
                self.displayed_art_url = url
                return

            # Otherwise fetch it
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=3) as response:
                image_bytes = response.read()

            image_file: PILImage = Image.open(BytesIO(image_bytes))
            size: tuple[int, int] = (300, 300)
            resized_image = resize_image(image_file, size)

            png_buffer = BytesIO()
            resized_image.save(png_buffer, format="PNG")

            download_pixmap = QPixmap()
            download_pixmap.loadFromData(png_buffer.getvalue())

            self.art_cache[url] = download_pixmap
            self.database.insert_artwork_data(url, png_buffer.getvalue())

            album_label.setPixmap(download_pixmap)
            self.displayed_art_url = url

        except Exception as e:
            print("Album load error:", e)


def resize_image(image: PILImage, size: tuple[int, int]) -> PILImage:
    """
    Resize a Pillow image to the requested dimensions.

    Kept separate from the main album-loading function to isolate
    image manipulation logic.
    """
    return image.resize(size)  # pyright: ignore[reportUnknownMemberType]
