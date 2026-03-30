# Edited by Claude Opus 4.6
"""Repository for Playlist entities."""

from src.models.playlist import Playlist
from src.repositories.db import get_connection

# Explicit column list to avoid column-order issues after ALTER TABLE migrations
_PLAYLIST_COLS = (
    "id, name, book, playlist_type, chapter_start, verse_start, "
    "chapter_end, verse_end, youtube_playlist_id, created_at"
)


class PlaylistRepository:
    """CRUD operations for the playlists table."""

    def insert(self, playlist: Playlist) -> Playlist:
        """Insert a new playlist and return it with the generated id."""
        conn = get_connection()
        result = conn.execute(
            """
            INSERT INTO playlists (name, book, playlist_type, chapter_start, verse_start, chapter_end, verse_end, youtube_playlist_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            [
                playlist.name,
                playlist.book,
                playlist.playlist_type.value,
                playlist.chapter_start,
                playlist.verse_start,
                playlist.chapter_end,
                playlist.verse_end,
                playlist.youtube_playlist_id,
            ],
        ).fetchone()
        playlist.id = result[0]
        return playlist

    def get_by_id(self, playlist_id: int) -> Playlist | None:
        """Get a playlist by id."""
        conn = get_connection()
        row = conn.execute(
            f"SELECT {_PLAYLIST_COLS} FROM playlists WHERE id = ?",
            [playlist_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def get_by_name(self, name: str) -> Playlist | None:
        """Get a playlist by name."""
        conn = get_connection()
        row = conn.execute(
            f"SELECT {_PLAYLIST_COLS} FROM playlists WHERE name = ?",
            [name],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def list_all(self) -> list[Playlist]:
        """List all playlists."""
        conn = get_connection()
        rows = conn.execute(
            f"SELECT {_PLAYLIST_COLS} FROM playlists ORDER BY id"
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, playlist: Playlist) -> None:
        """Update an existing playlist."""
        conn = get_connection()
        conn.execute(
            """
            UPDATE playlists
            SET name = ?, book = ?, playlist_type = ?, chapter_start = ?, verse_start = ?,
                chapter_end = ?, verse_end = ?, youtube_playlist_id = ?
            WHERE id = ?
            """,
            [
                playlist.name,
                playlist.book,
                playlist.playlist_type.value,
                playlist.chapter_start,
                playlist.verse_start,
                playlist.chapter_end,
                playlist.verse_end,
                playlist.youtube_playlist_id,
                playlist.id,
            ],
        )

    def delete(self, playlist_id: int) -> None:
        """Delete a playlist by id."""
        conn = get_connection()
        conn.execute("DELETE FROM playlists WHERE id = ?", [playlist_id])

    @staticmethod
    def _row_to_model(row: tuple) -> Playlist:
        """Convert a database row to a Playlist model."""
        return Playlist(
            id=row[0],
            name=row[1],
            book=row[2],
            playlist_type=row[3],
            chapter_start=row[4],
            verse_start=row[5],
            chapter_end=row[6],
            verse_end=row[7],
            youtube_playlist_id=row[8],
            created_at=row[9],
        )
