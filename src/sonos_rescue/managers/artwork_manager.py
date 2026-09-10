from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import cast
from PIL import Image, ImageOps
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC as APICProtocol
from PIL.Image import Image as PILImage
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy
from soco import SoCo  # type: ignore[import-untyped]
from urllib.request import Request, urlopen

from sonos_rescue.database.database import ArtworkDatabase


@dataclass(frozen=True)
class ArtResult:
    """Immutable result of an artwork retrieval operation."""

    art_url: str | None  # fully-resolved URL (None if no valid art)
    art_bytes: bytes | None  # PNG bytes ready to hand to QPixmap.loadFromData
    is_new: (
        bool  # True if freshly fetched over HTTP, False if it came from the DB cache
    )


class ArtworkManager:
    """
    Manages album artwork retrieval, caching, and display for Sonos devices.
    """

    MAX_CACHE = 20

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

    def resolve_and_fetch_art(self, url: str, speaker: SoCo) -> ArtResult:
        """
        Resolve an artwork URL and fetch its bytes.

        Safe to call from a worker thread: touches only plain data and the
        thread-safe artwork database, never QPixmap/QLabel.

        Args:
            url (str): The URL of the album artwork.
            speaker (SoCo): The Sonos speaker instance.
        """
        try:
            if not url or url == "None":
                return ArtResult(None, None, False)

            if not url.startswith("http"):
                speaker_ip = cast(str, speaker.ip_address)
                url = f"http://{speaker_ip}:1400{url}"

            if not url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                return ArtResult(None, None, False)

            # if the artwork is already cached in the database, use that
            cached_bytes = self.database.get_artwork_data(url)
            if cached_bytes is not None:
                return ArtResult(url, cached_bytes, is_new=False)

            # Otherwise fetch it
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=3) as response:
                image_bytes = response.read()

            image_file: PILImage = Image.open(BytesIO(image_bytes))
            size: tuple[int, int] = (500, 500)
            resized_image = ImageOps.fit(image_file, size, Image.Resampling.LANCZOS)

            png_buffer = BytesIO()
            resized_image.save(png_buffer, format="PNG")

            self.database.insert_artwork_data(url, png_buffer.getvalue())

            return ArtResult(url, png_buffer.getvalue(), is_new=True)

        except Exception as e:
            print("Error loading artwork:", e)

        return ArtResult(None, None, False)

    def set_album_art(self, album_label: QLabel, pixmap: QPixmap) -> QLabel:
        """
        Set the album art on the given QLabel.

        The image is expected to already be square-cropped to 500x500 before
        it reaches the label, so the label must not stretch it during display.

        Args:
            album_label (QLabel): The QLabel widget to display the artwork.
            pixmap (QPixmap): The QPixmap containing the artwork.
        """
        album_label.setPixmap(pixmap)
        album_label.setFixedSize(500, 500)
        album_label.setMinimumSize(500, 500)
        album_label.setMaximumSize(500, 500)
        album_label.setScaledContents(False)
        album_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return album_label


def resize_image(image: PILImage, size: tuple[int, int]) -> PILImage:
    """
    Resize a Pillow image to the requested dimensions.

    Kept separate from the main album-loading function to isolate
    image manipulation logic.
    """
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
