# Edited by Claude Opus 4.6
"""DuckDB connection manager and schema initialization."""

import atexit
import logging
import threading

import duckdb

from src.lib.config import get_db_path

logger = logging.getLogger(__name__)

_local = threading.local()


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Get a thread-local DuckDB connection, creating if needed.

    Args:
        read_only: Open in read-only mode (allows concurrent access).
    """
    # Edited by Claude Opus 4.6
    attr = "conn_ro" if read_only else "conn"
    if not hasattr(_local, attr) or getattr(_local, attr) is None:
        db_path = get_db_path()
        logger.debug(f"{db_path=}, {read_only=}")
        conn = duckdb.connect(str(db_path), read_only=read_only)
        if not read_only:
            ensure_schema(conn)
        setattr(_local, attr, conn)
    return getattr(_local, attr)


def close_connection() -> None:
    """Close all thread-local DuckDB connections if open."""
    # Edited by Claude Opus 4.6 - close both write and read-only connections
    for attr in ("conn", "conn_ro"):
        conn = getattr(_local, attr, None)
        if conn is not None:
            conn.close()
            setattr(_local, attr, None)


atexit.register(close_connection)


def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create tables if they don't exist."""
    # Sequences for auto-increment PKs
    for seq in (
        "seq_playlists", "seq_alyot", "seq_alya_audio", "seq_alya_videos",
        "seq_alignment_runs", "seq_alya_ranges", "seq_pasuk_alignments",
        # YouTube sequences (added by Claude Sonnet 4.5)
        "seq_youtube_thumbnails", "seq_youtube_uploads", "seq_youtube_playlist_meta", "seq_youtube_keywords"
    ):
        conn.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq}")

    # Edited by Claude Opus 4.6 — added playlist_type for megillot support
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_playlists'),
            name VARCHAR NOT NULL UNIQUE,
            book VARCHAR NOT NULL,
            playlist_type VARCHAR NOT NULL DEFAULT 'parasha',
            chapter_start INTEGER NOT NULL CHECK (chapter_start > 0),
            verse_start INTEGER NOT NULL CHECK (verse_start > 0),
            chapter_end INTEGER NOT NULL CHECK (chapter_end > 0),
            verse_end INTEGER NOT NULL CHECK (verse_end > 0),
            youtube_playlist_id VARCHAR,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alyot (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_alyot'),
            playlist_id INTEGER NOT NULL REFERENCES playlists(id),
            name VARCHAR NOT NULL,
            order_num INTEGER NOT NULL CHECK (order_num BETWEEN 1 AND 30),
            state VARCHAR NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            UNIQUE (playlist_id, order_num)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alya_ranges (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_alya_ranges'),
            alya_id INTEGER NOT NULL REFERENCES alyot(id),
            range_order INTEGER NOT NULL CHECK (range_order >= 1),
            book VARCHAR NOT NULL,
            chapter_start INTEGER NOT NULL CHECK (chapter_start > 0),
            verse_start INTEGER NOT NULL CHECK (verse_start > 0),
            chapter_end INTEGER NOT NULL CHECK (chapter_end > 0),
            verse_end INTEGER NOT NULL CHECK (verse_end > 0),
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            UNIQUE (alya_id, range_order)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alya_audio (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_alya_audio'),
            alya_id INTEGER NOT NULL UNIQUE REFERENCES alyot(id),
            file_path VARCHAR NOT NULL,
            format VARCHAR NOT NULL,
            duration_seconds DOUBLE NOT NULL CHECK (duration_seconds > 0),
            sample_rate INTEGER NOT NULL CHECK (sample_rate BETWEEN 16000 AND 48000),
            channels INTEGER NOT NULL CHECK (channels BETWEEN 1 AND 2),
            attribution VARCHAR DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alya_videos (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_alya_videos'),
            alya_id INTEGER NOT NULL UNIQUE REFERENCES alyot(id),
            file_path VARCHAR NOT NULL,
            format VARCHAR NOT NULL DEFAULT 'mp4',
            resolution_w INTEGER NOT NULL,
            resolution_h INTEGER NOT NULL,
            frame_rate INTEGER NOT NULL DEFAULT 30,
            codec VARCHAR NOT NULL DEFAULT 'h264',
            duration_seconds DOUBLE NOT NULL CHECK (duration_seconds > 0),
            youtube_video_id VARCHAR,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alignment_runs (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_alignment_runs'),
            alya_audio_id INTEGER NOT NULL REFERENCES alya_audio(id),
            alignment_quality DOUBLE NOT NULL CHECK (alignment_quality BETWEEN 0.0 AND 1.0),
            verse_count INTEGER NOT NULL CHECK (verse_count > 0),
            manually_corrected BOOLEAN NOT NULL DEFAULT false,
            corrected_at TIMESTAMP,
            backup_path VARCHAR,
            original_quality DOUBLE CHECK (original_quality BETWEEN 0.0 AND 1.0),
            generated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pasuk_alignments (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_pasuk_alignments'),
            alignment_run_id INTEGER NOT NULL REFERENCES alignment_runs(id),
            reference VARCHAR NOT NULL,
            hebrew_text VARCHAR NOT NULL,
            verse_order INTEGER NOT NULL CHECK (verse_order >= 1),
            start_time DOUBLE NOT NULL CHECK (start_time >= 0),
            end_time DOUBLE NOT NULL,
            confidence DOUBLE NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
            original_start_time DOUBLE,
            original_end_time DOUBLE,
            manually_corrected BOOLEAN NOT NULL DEFAULT false,
            UNIQUE (alignment_run_id, verse_order)
        )
    """)

    # YouTube Integration Tables (added by Claude Sonnet 4.5)
    # Replaces JSON-based caching with DuckDB persistence

    conn.execute("""
        CREATE TABLE IF NOT EXISTS youtube_thumbnails (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_youtube_thumbnails'),
            video_id VARCHAR NOT NULL UNIQUE,
            original_url VARCHAR NOT NULL,
            cached_path VARCHAR NOT NULL,
            title VARCHAR,
            downloaded_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS youtube_uploads (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_youtube_uploads'),
            alya_video_id INTEGER NOT NULL REFERENCES alya_videos(id),
            old_youtube_video_id VARCHAR,
            new_youtube_video_id VARCHAR NOT NULL,
            thumbnail_restored BOOLEAN NOT NULL DEFAULT false,
            added_to_playlist BOOLEAN NOT NULL DEFAULT false,
            upload_status VARCHAR NOT NULL DEFAULT 'pending',
            error_message VARCHAR,
            uploaded_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            completed_at TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS youtube_playlist_meta (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_youtube_playlist_meta'),
            playlist_id INTEGER NOT NULL UNIQUE REFERENCES playlists(id),
            youtube_playlist_id VARCHAR NOT NULL UNIQUE,
            title VARCHAR NOT NULL,
            description VARCHAR,
            privacy_status VARCHAR NOT NULL DEFAULT 'unlisted',
            tradition VARCHAR NOT NULL DEFAULT 'Ashkenaz',
            video_count INTEGER NOT NULL DEFAULT 0,
            expected_video_count INTEGER NOT NULL DEFAULT 7,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    # YouTube Keywords Table (added by Claude Sonnet 4.5)
    # Stores tiered keyword strategy for SEO optimization
    conn.execute("""
        CREATE TABLE IF NOT EXISTS youtube_keywords (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_youtube_keywords'),
            alya_id INTEGER NOT NULL UNIQUE REFERENCES alyot(id),
            tier1_keywords VARCHAR[] NOT NULL,
            tier2_keywords VARCHAR[] NOT NULL,
            tier3_keywords VARCHAR[] NOT NULL,
            tier4_keywords VARCHAR[] NOT NULL,
            combined_tags VARCHAR NOT NULL,
            tag_count INTEGER NOT NULL,
            char_count INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)

    # YouTube indexes for performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_thumbnails_video_id ON youtube_thumbnails(video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_uploads_alya_video ON youtube_uploads(alya_video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_uploads_status ON youtube_uploads(upload_status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_playlist_meta_playlist ON youtube_playlist_meta(playlist_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_keywords_alya ON youtube_keywords(alya_id)")

    # Edited by Claude Opus 4.6 — migrations for megillot support
    _migrate_playlists_add_type(conn)
    # Edited by Claude Sonnet 4.5 — migrations for local thumbnail support
    _migrate_alya_videos_add_thumbnail(conn)


def _migrate_playlists_add_type(conn: duckdb.DuckDBPyConnection) -> None:
    """Add playlist_type column to playlists if missing (migration)."""
    cols = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'playlists'"
        ).fetchall()
    }
    if "playlist_type" not in cols:
        logger.info("Migrating playlists table: adding playlist_type column")
        conn.execute("ALTER TABLE playlists ADD COLUMN playlist_type VARCHAR DEFAULT 'parasha'")
        conn.execute("UPDATE playlists SET playlist_type = 'parasha' WHERE playlist_type IS NULL")


def _migrate_alya_videos_add_thumbnail(conn: duckdb.DuckDBPyConnection) -> None:
    """Add thumbnail_path column to alya_videos table (migration)."""
    cols = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'alya_videos'"
        ).fetchall()
    }
    if "thumbnail_path" not in cols:
        logger.info("Migrating alya_videos table: adding thumbnail_path column")
        conn.execute("ALTER TABLE alya_videos ADD COLUMN thumbnail_path VARCHAR")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alya_videos_thumbnail "
            "ON alya_videos(thumbnail_path)"
        )
