# Data Model: DuckDB-Backed Entities

<!-- Edited by Claude Opus 4.6 -->

**Date**: 2026-03-15
**Feature**: 002-manual-alignment-correction
**Purpose**: Define flat, DuckDB-storable entities replacing nested Pydantic models
**Source of truth**: `tmp/db_erd.md` (ERD v2)

## Design Rationale

The original models (Parasha, Aliyah, Pasuk, AudioSource, SynchronizedVideo, TimestampMap)
used nested Pydantic structures unsuitable for database storage. The new models are flat
entities with foreign key relationships, designed for DuckDB persistence via a repository
pattern.

Key design changes from v1:
1. **Per-pasuk alignment** — `pasuk_alignments` table stores individual verse timestamps (replaces `timestamps_json` blob)
2. **alignment_runs** links to `alya_audio` (the source audio) and produces many `pasuk_alignments`
3. **Haftara** is just another aliyah (`order_num=9`), no separate entity
4. **alya_ranges** — supports multiple non-consecutive verse ranges per alya (needed for compound Haftarot)

## Entity Mapping (Old → New)

| Old Model         | New Model        | Key Change                                     |
|-------------------|------------------|-------------------------------------------------|
| Parasha           | Playlist         | Renamed to reflect YouTube playlist purpose     |
| Aliyah            | Alya             | Flat, references playlist_id instead of nesting |
| AudioSource       | AlyaAudio        | References alya_id, no file existence validator  |
| SynchronizedVideo | AlyaVideo        | References alya_id (1:1), simplified validators  |
| TimestampMap      | AlignmentRun + PasukAlignment | Split: run metadata + per-verse rows |
| Pasuk             | (kept as-is)     | Used transiently for text fetching, not stored  |
| AliyahRange       | AlyaRange (DB)   | Moved from TOML config to `alya_ranges` table   |
| HebrewTextSource  | (kept as-is)     | Protocol, not a data model                      |

## New Entities

### Playlist

Represents a YouTube playlist for a Parasha (weekly Torah portion).

**Table**: `playlists`

| Column              | Type      | Constraints               |
|---------------------|-----------|---------------------------|
| id                  | INTEGER   | PK, auto-increment        |
| name                | VARCHAR   | NOT NULL, UNIQUE          |
| book                | VARCHAR   | NOT NULL                  |
| chapter_start       | INTEGER   | NOT NULL, > 0             |
| verse_start         | INTEGER   | NOT NULL, > 0             |
| chapter_end         | INTEGER   | NOT NULL, > 0             |
| verse_end           | INTEGER   | NOT NULL, > 0             |
| youtube_playlist_id | VARCHAR   | NULLABLE (set after upload) |
| created_at          | TIMESTAMP | NOT NULL, DEFAULT now()   |

### Alya

Core processing unit — one Aliyah within a Parasha. Haftara is stored as `order_num=9`.

**Table**: `alyot`

| Column         | Type      | Constraints                          |
|----------------|-----------|--------------------------------------|
| id             | INTEGER   | PK, auto-increment                   |
| playlist_id    | INTEGER   | FK → playlists.id, NOT NULL          |
| name           | VARCHAR   | NOT NULL (Hebrew name, e.g. "ראשון") |
| order_num      | INTEGER   | NOT NULL, 1-9 (9 = haftara)         |
| state          | VARCHAR   | NOT NULL, DEFAULT 'pending'          |
| created_at     | TIMESTAMP | NOT NULL, DEFAULT now()              |

**Unique**: (playlist_id, order_num)

**State values**: pending, aligning, aligned, rendering, completed, failed

### AlyaRange

Verse range for an alya. Torah aliyot have exactly one range; Haftarot may have
multiple ranges for compound readings (e.g. Jeremiah 2:4-28 + 3:4).

**Table**: `alya_ranges`

| Column        | Type      | Constraints                    |
|---------------|-----------|--------------------------------|
| id            | INTEGER   | PK, auto-increment             |
| alya_id       | INTEGER   | FK → alyot.id, NOT NULL        |
| range_order   | INTEGER   | NOT NULL, 1-based              |
| book          | VARCHAR   | NOT NULL (e.g. "Deuteronomy")  |
| chapter_start | INTEGER   | NOT NULL, > 0                  |
| verse_start   | INTEGER   | NOT NULL, > 0                  |
| chapter_end   | INTEGER   | NOT NULL, > 0                  |
| verse_end     | INTEGER   | NOT NULL, > 0                  |
| created_at    | TIMESTAMP | NOT NULL, DEFAULT now()        |

**Unique**: (alya_id, range_order)

**Example — compound Haftara (Masei, Ashkenazi)**:

| alya (Masei Haftara) | range_order | book     | range          |
|----------------------|-------------|----------|----------------|
| id=7                 | 1           | Jeremiah | 2:4 – 2:28     |
| id=7                 | 2           | Jeremiah | 3:4 – 3:4      |

The text fetcher makes one Sefaria API call per range and concatenates the results.

### AlyaAudio

Audio file metadata for an Alya.

**Table**: `alya_audio`

| Column           | Type      | Constraints                       |
|------------------|-----------|-----------------------------------|
| id               | INTEGER   | PK, auto-increment                |
| alya_id          | INTEGER   | FK → alyot.id, NOT NULL, UNIQUE   |
| file_path        | VARCHAR   | NOT NULL                          |
| format           | VARCHAR   | NOT NULL (mp3, mp4, wav)          |
| duration_seconds | DOUBLE    | NOT NULL, > 0                     |
| sample_rate      | INTEGER   | NOT NULL, 16000-48000             |
| channels         | INTEGER   | NOT NULL, 1-2                     |
| attribution      | VARCHAR   | DEFAULT ''                        |
| created_at       | TIMESTAMP | NOT NULL, DEFAULT now()           |

### AlyaVideo

Rendered video file for an Alya. One-to-one with Alya — a re-render replaces the existing video.

**Table**: `alya_videos`

| Column           | Type      | Constraints                       |
|------------------|-----------|-----------------------------------|
| id               | INTEGER   | PK, auto-increment                |
| alya_id          | INTEGER   | FK → alyot.id, NOT NULL, UNIQUE   |
| file_path        | VARCHAR   | NOT NULL                          |
| format           | VARCHAR   | NOT NULL, DEFAULT 'mp4'           |
| resolution_w     | INTEGER   | NOT NULL                          |
| resolution_h     | INTEGER   | NOT NULL                          |
| frame_rate       | INTEGER   | NOT NULL, DEFAULT 30              |
| codec            | VARCHAR   | NOT NULL, DEFAULT 'h264'          |
| duration_seconds | DOUBLE    | NOT NULL, > 0                     |
| youtube_video_id | VARCHAR   | NULLABLE (set after upload)       |
| created_at       | TIMESTAMP | NOT NULL, DEFAULT now()           |

### AlignmentRun

Result of a forced alignment run. Links to `alya_audio` (the source audio), not
directly to `alyot`, because the audio file is the actual input to the alignment engine.
One audio → many alignment attempts.

**Table**: `alignment_runs`

| Column              | Type      | Constraints                       |
|---------------------|-----------|-----------------------------------|
| id                  | INTEGER   | PK, auto-increment                |
| alya_audio_id       | INTEGER   | FK → alya_audio.id, NOT NULL      |
| alignment_quality   | DOUBLE    | NOT NULL, 0.0-1.0                 |
| verse_count         | INTEGER   | NOT NULL, > 0                     |
| manually_corrected  | BOOLEAN   | NOT NULL, DEFAULT false           |
| corrected_at        | TIMESTAMP | NULLABLE                          |
| backup_path         | VARCHAR   | NULLABLE                          |
| original_quality    | DOUBLE    | NULLABLE, 0.0-1.0                 |
| generated_at        | TIMESTAMP | NOT NULL, DEFAULT now()           |

### PasukAlignment

Individual verse alignment within an alignment run. Each verse gets its own row,
enabling SQL queries per verse and individual correction tracking.

**Table**: `pasuk_alignments`

| Column              | Type      | Constraints                       |
|---------------------|-----------|-----------------------------------|
| id                  | INTEGER   | PK, auto-increment                |
| alignment_run_id    | INTEGER   | FK → alignment_runs.id, NOT NULL  |
| reference           | VARCHAR   | NOT NULL (e.g. "Deuteronomy 32:1")|
| hebrew_text         | VARCHAR   | NOT NULL (verse text with nikkud) |
| verse_order         | INTEGER   | NOT NULL (position within alya)   |
| start_time          | DOUBLE    | NOT NULL, >= 0 (seconds)          |
| end_time            | DOUBLE    | NOT NULL, > start_time (seconds)  |
| confidence          | DOUBLE    | NOT NULL, 0.0-1.0                 |
| original_start_time | DOUBLE    | NULLABLE (pre-correction value)   |
| original_end_time   | DOUBLE    | NULLABLE (pre-correction value)   |
| manually_corrected  | BOOLEAN   | NOT NULL, DEFAULT false           |

**Unique**: (alignment_run_id, verse_order)

## Entity Relationship Diagram

```text
Playlist (1) ────< (N) Alya
                        │
                        ├────< (N) AlyaRange     (1:N, 1+ verse ranges)
                        ├──── (1) AlyaAudio      (1:1)
                        │           │
                        │           └────< (N) AlignmentRun (1:N, one per attempt)
                        │                        │
                        │                        └────< (N) PasukAlignment (1:N, one per verse)
                        │
                        └──── (1) AlyaVideo      (1:1, re-render replaces)
```

See `tmp/db_erd.md` for the full Mermaid ERD.

## Retained Models (Not Stored in DB)

- **Pasuk** — Used transiently during text fetching from Sefaria
- **HebrewTextSource** — Protocol interface for text retrieval
- **VerseTimestamp** — Transient model used during alignment engine processing

## Deleted Models

- **Parasha** — Replaced by Playlist
- **Aliyah** — Replaced by Alya
- **AudioSource** — Replaced by AlyaAudio
- **SynchronizedVideo** — Replaced by AlyaVideo
- **TimestampMap** — Replaced by AlignmentRun + PasukAlignment

## Correction Tracking

Manual correction metadata is tracked at two levels:

### Per-run level (alignment_runs)
- `manually_corrected` — whether any verse in this run has been corrected
- `corrected_at` — when last correction was applied
- `backup_path` — path to backup of original alignment
- `original_quality` — alignment quality before corrections

### Per-verse level (pasuk_alignments)
- `original_start_time` / `original_end_time` — pre-correction values for comparison/revert
- `manually_corrected` — whether this specific verse has been corrected

The **ValidationResult** and **Violation** models remain as transient Pydantic
models used by the validation service (not stored in DB).

## DuckDB Connection Management

```python
# src/repositories/db.py
# Connection manager with schema auto-migration

get_connection() -> duckdb.DuckDBPyConnection  # Thread-local connection
ensure_schema()                                 # CREATE TABLE IF NOT EXISTS
```

## Repository Pattern

Each entity gets a repository class in `src/repositories/`:

```text
src/repositories/
├── db.py                    # Connection manager + schema
├── playlist_repo.py         # PlaylistRepository
├── alya_repo.py             # AlyaRepository
├── alya_range_repo.py       # AlyaRangeRepository
├── alya_audio_repo.py       # AlyaAudioRepository
├── alya_video_repo.py       # AlyaVideoRepository
├── alignment_repo.py        # AlignmentRunRepository
└── pasuk_alignment_repo.py  # PasukAlignmentRepository
```

Each repository provides: `insert()`, `get_by_id()`, `list_all()`, `update()`, `delete()`.
