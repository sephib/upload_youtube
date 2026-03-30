# Edited by Claude Opus 4.6
"""Local thumbnail discovery service for Torah readings."""

import re
from pathlib import Path

from src.lib.logging import get_logger
from src.models.alya import Alya
from src.models.playlist import Playlist, PlaylistType

logger = get_logger(__name__)

# Matches filenames like "Megillat_Kohelet_1.jpg" or "Haazinu_3.jpg"
_NUMBERED_JPG_RE = re.compile(r"^(.+_)(\d+)\.jpg$")

# English book name -> Hebrew folder name
_BOOK_TO_FOLDER: dict[str, str] = {
    "Genesis": "ספר בראשית",
    "Exodus": "ספר שמות",
    "Leviticus": "ספר ויקרא",
    "Numbers": "ספר במדבר",
    "Deuteronomy": "ספר דברים",
}

# Hebrew alya name -> thumbnail suffix for special alyot
_SPECIAL_ALYA_SUFFIX: dict[str, str] = {
    "מפטיר": "Maftir",
    "הפטרה": "Haftara",
}


class LocalThumbnailService:
    """Finds local thumbnail files for Torah readings (parashot and megillot)."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path("data/torah_read")

    def find_thumbnail(self, playlist: Playlist, alya: Alya) -> Path | None:
        """Find thumbnail file for an alya.

        Returns None if thumbnail file or folder not found.
        """
        if playlist.playlist_type == PlaylistType.MEGILLAH:
            return self._find_megillah_thumbnail(playlist, alya)
        return self._find_parasha_thumbnail(playlist, alya)

    def _find_parasha_thumbnail(self, playlist: Playlist, alya: Alya) -> Path | None:
        """Find thumbnail for a parasha alya.

        Folder: {base_dir}/{book_folder}/{parasha_name}/
        File: {Pattern}_{order_num}.jpg or {Pattern}_{Maftir|Haftara}.jpg
        """
        book_folder = _BOOK_TO_FOLDER.get(playlist.book)
        if not book_folder:
            logger.warning(f"No folder mapping for {playlist.book=}")
            return None

        folder = self.base_dir / book_folder / playlist.name
        if not folder.is_dir():
            logger.warning(f"{folder=} not found")
            return None

        base_pattern = self._find_jpg_pattern(folder)
        if not base_pattern:
            return None

        # Special alyot (מפטיר, הפטרה) use named suffixes
        special_suffix = _SPECIAL_ALYA_SUFFIX.get(alya.name)
        if special_suffix:
            thumbnail_path = folder / f"{base_pattern}{special_suffix}.jpg"
        else:
            thumbnail_path = folder / f"{base_pattern}{alya.order_num}.jpg"

        if thumbnail_path.exists():
            logger.debug(f"Found thumbnail: {thumbnail_path.name}")
            return thumbnail_path

        logger.warning(f"Thumbnail not found: {thumbnail_path}")
        return None

    def _find_megillah_thumbnail(self, playlist: Playlist, alya: Alya) -> Path | None:
        """Find thumbnail for a megillah chapter.

        Folder: {base_dir}/מגילות/{megillah_name}/
        File: {Pattern}_{order_num}.jpg
        """
        folder = self.base_dir / "מגילות" / playlist.name
        if not folder.is_dir():
            logger.warning(f"{folder=} not found")
            return None

        base_pattern = self._find_jpg_pattern(folder)
        if not base_pattern:
            return None

        thumbnail_path = folder / f"{base_pattern}{alya.order_num}.jpg"

        if thumbnail_path.exists():
            logger.debug(f"Found thumbnail: {thumbnail_path.name}")
            return thumbnail_path

        logger.warning(f"Thumbnail not found: {thumbnail_path}")
        return None

    def _find_jpg_pattern(self, folder: Path) -> str | None:
        """Extract base pattern from JPG files.

        Returns:
            Base pattern like "Haazinu_" or "Megillat_Shir_Hashirim_" or None.
        """
        jpgs = sorted(folder.glob("*.jpg"))
        if not jpgs:
            logger.warning(f"No JPG files in {folder}")
            return None

        for jpg in jpgs:
            match = _NUMBERED_JPG_RE.match(jpg.name)
            if match:
                base_pattern = match.group(1)
                logger.debug(f"Extracted {base_pattern=} from {jpg.name}")
                return base_pattern

        logger.warning(f"No JPG files match expected pattern in {folder}")
        return None
