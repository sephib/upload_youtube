# Edited by Claude Opus 4.6
"""DuckDB connection manager and schema initialization."""

import logging
import threading

import duckdb

from src.lib.config import get_db_path

logger = logging.getLogger(__name__)

_local = threading.local()


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get a thread-local DuckDB connection, creating if needed."""
    if not hasattr(_local, "conn") or _local.conn is None:
        db_path = get_db_path()
        logger.debug(f"{db_path=}")
        _local.conn = duckdb.connect(str(db_path))
        ensure_schema(_local.conn)
    return _local.conn


def close_connection() -> None:
    """Close the thread-local DuckDB connection if open."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create tables if they don't exist."""
    # Sequences for auto-increment PKs
    for seq in (
        "seq_playlists", "seq_alyot", "seq_alya_audio", "seq_alya_videos",
        "seq_alignment_runs", "seq_alya_ranges", "seq_pasuk_alignments",
        # YouTube sequences (added by Claude Sonnet 4.5)
        "seq_youtube_thumbnails", "seq_youtube_uploads", "seq_youtube_playlist_meta"
    ):
        conn.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq}")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_playlists'),
            name VARCHAR NOT NULL UNIQUE,
            book VARCHAR NOT NULL,
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
            order_num INTEGER NOT NULL CHECK (order_num BETWEEN 1 AND 9),
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

    # YouTube indexes for performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_thumbnails_video_id ON youtube_thumbnails(video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_uploads_alya_video ON youtube_uploads(alya_video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_uploads_status ON youtube_uploads(upload_status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_playlist_meta_playlist ON youtube_playlist_meta(playlist_id)")
