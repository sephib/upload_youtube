# Edited by Claude Opus 4.6
"""Unit tests for LocalThumbnailService."""

from pathlib import Path

import pytest

from src.models.alya import Alya
from src.models.playlist import Playlist, PlaylistType
from src.services.local_thumbnail_service import LocalThumbnailService


def test_find_thumbnail_for_megillah_success(tmp_path):
    """Happy path: thumbnail found for megillah chapter."""
    megillah_dir = tmp_path / "מגילות" / "שיר השירים"
    megillah_dir.mkdir(parents=True)
    (megillah_dir / "Megillat_Shir_Hashirim_1.jpg").touch()
    (megillah_dir / "Megillat_Shir_Hashirim_2.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=1,
        name="שיר השירים",
        book="Song of Songs",
        playlist_type=PlaylistType.MEGILLAH,
        chapter_start=1,
        verse_start=1,
        chapter_end=8,
        verse_end=14,
    )
    alya = Alya(id=1, playlist_id=1, name="פרק א", order_num=1)

    result = service.find_thumbnail(playlist, alya)
    assert result == megillah_dir / "Megillat_Shir_Hashirim_1.jpg"


def test_find_thumbnail_for_parasha_success(tmp_path):
    """Happy path: thumbnail found for parasha alya."""
    parasha_dir = tmp_path / "ספר דברים" / "האזינו"
    parasha_dir.mkdir(parents=True)
    (parasha_dir / "Haazinu_1.jpg").touch()
    (parasha_dir / "Haazinu_2.jpg").touch()
    (parasha_dir / "Haazinu_Maftir.jpg").touch()
    (parasha_dir / "Haazinu_Haftara.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=1,
        name="האזינו",
        book="Deuteronomy",
        playlist_type=PlaylistType.PARASHA,
        chapter_start=32,
        verse_start=1,
        chapter_end=32,
        verse_end=52,
    )
    alya = Alya(id=1, playlist_id=1, name="ראשון", order_num=1)

    result = service.find_thumbnail(playlist, alya)
    assert result == parasha_dir / "Haazinu_1.jpg"


def test_find_thumbnail_for_parasha_maftir(tmp_path):
    """Maftir alya finds _Maftir.jpg thumbnail."""
    parasha_dir = tmp_path / "ספר דברים" / "האזינו"
    parasha_dir.mkdir(parents=True)
    (parasha_dir / "Haazinu_1.jpg").touch()
    (parasha_dir / "Haazinu_Maftir.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=1,
        name="האזינו",
        book="Deuteronomy",
        playlist_type=PlaylistType.PARASHA,
        chapter_start=32,
        verse_start=1,
        chapter_end=32,
        verse_end=52,
    )
    alya = Alya(id=8, playlist_id=1, name="מפטיר", order_num=8)

    result = service.find_thumbnail(playlist, alya)
    assert result == parasha_dir / "Haazinu_Maftir.jpg"


def test_find_thumbnail_for_parasha_haftara(tmp_path):
    """Haftara alya finds _Haftara.jpg thumbnail."""
    parasha_dir = tmp_path / "ספר דברים" / "האזינו"
    parasha_dir.mkdir(parents=True)
    (parasha_dir / "Haazinu_1.jpg").touch()
    (parasha_dir / "Haazinu_Haftara.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=1,
        name="האזינו",
        book="Deuteronomy",
        playlist_type=PlaylistType.PARASHA,
        chapter_start=32,
        verse_start=1,
        chapter_end=32,
        verse_end=52,
    )
    alya = Alya(id=9, playlist_id=1, name="הפטרה", order_num=9)

    result = service.find_thumbnail(playlist, alya)
    assert result == parasha_dir / "Haazinu_Haftara.jpg"


def test_find_thumbnail_for_parasha_missing_folder(tmp_path):
    """Parasha folder not found returns None."""
    (tmp_path / "ספר דברים").mkdir()
    # No האזינו subfolder

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=1,
        name="האזינו",
        book="Deuteronomy",
        playlist_type=PlaylistType.PARASHA,
        chapter_start=32,
        verse_start=1,
        chapter_end=32,
        verse_end=52,
    )
    alya = Alya(id=1, playlist_id=1, name="ראשון", order_num=1)

    result = service.find_thumbnail(playlist, alya)
    assert result is None


def test_find_thumbnail_missing_folder():
    """Non-existent megillah folder returns None."""
    service = LocalThumbnailService(base_dir=Path("/nonexistent"))
    playlist = Playlist(
        id=1,
        name="שיר השירים",
        book="Song of Songs",
        playlist_type=PlaylistType.MEGILLAH,
        chapter_start=1,
        verse_start=1,
        chapter_end=8,
        verse_end=14,
    )
    alya = Alya(id=1, playlist_id=1, name="פרק א", order_num=1)

    result = service.find_thumbnail(playlist, alya)
    assert result is None


def test_find_thumbnail_missing_file(tmp_path):
    """Thumbnail file doesn't exist for chapter number."""
    megillah_dir = tmp_path / "מגילות" / "שיר השירים"
    megillah_dir.mkdir(parents=True)
    (megillah_dir / "Megillat_Shir_Hashirim_1.jpg").touch()
    # No file for chapter 5

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=1,
        name="שיר השירים",
        book="Song of Songs",
        playlist_type=PlaylistType.MEGILLAH,
        chapter_start=1,
        verse_start=1,
        chapter_end=8,
        verse_end=14,
    )
    alya = Alya(id=5, playlist_id=1, name="פרק ה", order_num=5)

    result = service.find_thumbnail(playlist, alya)
    assert result is None


def test_find_jpg_pattern_extraction_uppercase(tmp_path):
    """Pattern extraction works for uppercase 'Megillat'."""
    dir1 = tmp_path / "test1"
    dir1.mkdir()
    (dir1 / "Megillat_Shir_Hashirim_1.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    pattern = service._find_jpg_pattern(dir1)
    assert pattern == "Megillat_Shir_Hashirim_"


def test_find_jpg_pattern_extraction_lowercase(tmp_path):
    """Pattern extraction works for lowercase 'megilat'."""
    dir2 = tmp_path / "test2"
    dir2.mkdir()
    (dir2 / "megilat_ruth_1.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    pattern = service._find_jpg_pattern(dir2)
    assert pattern == "megilat_ruth_"


def test_find_jpg_pattern_no_jpgs(tmp_path):
    """No JPG files returns None."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    service = LocalThumbnailService(base_dir=tmp_path)
    pattern = service._find_jpg_pattern(empty_dir)
    assert pattern is None


def test_find_jpg_pattern_no_matching_pattern(tmp_path):
    """JPG files without numbered pattern returns None."""
    dir_no_pattern = tmp_path / "no_pattern"
    dir_no_pattern.mkdir()
    (dir_no_pattern / "ContactSheet-001.jpg").touch()
    (dir_no_pattern / "random.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    pattern = service._find_jpg_pattern(dir_no_pattern)
    assert pattern is None


def test_find_thumbnail_with_second_chapter(tmp_path):
    """Verify thumbnail matching works for chapter 2."""
    megillah_dir = tmp_path / "מגילות" / "רות"
    megillah_dir.mkdir(parents=True)
    (megillah_dir / "megilat_ruth_1.jpg").touch()
    (megillah_dir / "megilat_ruth_2.jpg").touch()
    (megillah_dir / "megilat_ruth_3.jpg").touch()

    service = LocalThumbnailService(base_dir=tmp_path)
    playlist = Playlist(
        id=2,
        name="רות",
        book="Ruth",
        playlist_type=PlaylistType.MEGILLAH,
        chapter_start=1,
        verse_start=1,
        chapter_end=4,
        verse_end=22,
    )
    alya = Alya(id=2, playlist_id=2, name="פרק ב", order_num=2)

    result = service.find_thumbnail(playlist, alya)
    assert result == megillah_dir / "megilat_ruth_2.jpg"
