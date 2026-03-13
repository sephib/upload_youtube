# Data Model: DuckDB-Backed Entities

<!-- Edited by Claude Opus 4.6 -->

**Date**: 2026-03-13
**Feature**: 002-manual-alignment-correction
**Purpose**: Define flat, DuckDB-storable entities replacing nested Pydantic models

## Design Rationale

The original models (Parasha, Aliyah, Pasuk, AudioSource, SynchronizedVideo, TimestampMap)
used nested Pydantic structures unsuitable for database storage. The new models are flat
entities with foreign key relationships, designed for DuckDB persistence via a repository
pattern.

## Entity Mapping (Old → New)

| Old Model         | New Model      | Key Change                                     |
|-------------------|----------------|-------------------------------------------------|
| Parasha           | Playlist       | Renamed to reflect YouTube playlist purpose     |
| Aliyah            | Alya           | Flat, references playlist_id instead of nesting |
| AudioSource       | AlyaAudio      | References alya_id, no file existence validator  |
| SynchronizedVideo | AlyaVideo      | References alya_id, simplified validators       |
| TimestampMap      | AlignmentRun   | References alya_id, stores alignment metadata   |
| Pasuk             | (kept as-is)   | Used transiently for text fetching, not stored  |
| AliyahRange       | (kept as-is)   | Config model, loaded from TOML                  |
| HebrewTextSource  | (kept as-is)   | Protocol, not a data model                      |

## New Entities

### Playlist

Represents a YouTube playlist for a Parasha (weekly Torah portion).

**Table**: `playlists`

| Column         | Type      | Constraints               |
|----------------|-----------|---------------------------|
| id             | INTEGER   | PK, auto-increment        |
| name           | VARCHAR   | NOT NULL, UNIQUE          |
| book           | VARCHAR   | NOT NULL                  |
| chapter_start  | INTEGER   | NOT NULL, > 0             |
| verse_start    | INTEGER   | NOT NULL, > 0             |
| chapter_end    | INTEGER   | NOT NULL, >= chapter_start|
| verse_end      | INTEGER   | NOT NULL, > 0             |
| youtube_playlist_id | VARCHAR | NULLABLE (set after upload) |
| created_at     | TIMESTAMP | NOT NULL, DEFAULT now()   |

### Alya

Core processing unit — one Aliyah within a Parasha.

**Table**: `alyot`

| Column         | Type      | Constraints                          |
|----------------|-----------|--------------------------------------|
| id             | INTEGER   | PK, auto-increment                   |
| playlist_id    | INTEGER   | FK → playlists.id, NOT NULL          |
| name           | VARCHAR   | NOT NULL (Hebrew name, e.g. "ראשון") |
| order_num      | INTEGER   | NOT NULL, 1-8                        |
| state          | VARCHAR   | NOT NULL, DEFAULT 'pending'          |
| created_at     | TIMESTAMP | NOT NULL, DEFAULT now()              |

**Unique**: (playlist_id, order_num)

**State values**: pending, aligning, aligned, rendering, completed, failed

### AlyaAudio

Audio file metadata for an Alya.

**Table**: `alya_audio`

| Column           | Type      | Constraints                  |
|------------------|-----------|------------------------------|
| id               | INTEGER   | PK, auto-increment           |
| alya_id          | INTEGER   | FK → alyot.id, NOT NULL, UNIQUE |
| file_path        | VARCHAR   | NOT NULL                     |
| format           | VARCHAR   | NOT NULL (mp3, mp4, wav)     |
| duration_seconds | DOUBLE    | NOT NULL, > 0                |
| sample_rate      | INTEGER   | NOT NULL, 16000-48000        |
| channels         | INTEGER   | NOT NULL, 1-2                |
| attribution      | VARCHAR   | DEFAULT ''                   |
| created_at       | TIMESTAMP | NOT NULL, DEFAULT now()      |

### AlyaVideo

Rendered video file for an Alya.

**Table**: `alya_videos`

| Column           | Type      | Constraints                     |
|------------------|-----------|---------------------------------|
| id               | INTEGER   | PK, auto-increment              |
| alya_id          | INTEGER   | FK → alyot.id, NOT NULL         |
| file_path        | VARCHAR   | NOT NULL                        |
| format           | VARCHAR   | NOT NULL, DEFAULT 'mp4'         |
| resolution_w     | INTEGER   | NOT NULL                        |
| resolution_h     | INTEGER   | NOT NULL                        |
| frame_rate       | INTEGER   | NOT NULL, DEFAULT 30            |
| codec            | VARCHAR   | NOT NULL, DEFAULT 'h264'        |
| duration_seconds | DOUBLE    | NOT NULL, > 0                   |
| youtube_video_id | VARCHAR   | NULLABLE (set after upload)     |
| created_at       | TIMESTAMP | NOT NULL, DEFAULT now()         |

### AlignmentRun

Result of a forced alignment run for an Alya.

**Table**: `alignment_runs`

| Column                | Type      | Constraints                  |
|-----------------------|-----------|------------------------------|
| id                    | INTEGER   | PK, auto-increment           |
| alya_id               | INTEGER   | FK → alyot.id, NOT NULL      |
| audio_file_path       | VARCHAR   | NOT NULL                     |
| audio_duration_seconds| DOUBLE    | NOT NULL, > 0                |
| alignment_quality     | DOUBLE    | NOT NULL, 0.0-1.0            |
| verse_count           | INTEGER   | NOT NULL, > 0                |
| timestamps_json       | VARCHAR   | NOT NULL (JSON array of VerseTimestamp) |
| manual_corrections    | INTEGER   | NOT NULL, DEFAULT 0          |
| manually_corrected    | BOOLEAN   | NOT NULL, DEFAULT false      |
| corrected_at          | TIMESTAMP | NULLABLE                     |
| backup_path           | VARCHAR   | NULLABLE                     |
| original_quality      | DOUBLE    | NULLABLE, 0.0-1.0            |
| generated_at          | TIMESTAMP | NOT NULL, DEFAULT now()      |

**Note**: `timestamps_json` stores the full `list[VerseTimestamp]` as a JSON string.
This keeps the schema simple while allowing DuckDB's JSON functions for queries.

## Entity Relationship Diagram

```text
Playlist (1) ────< (N) Alya
                        │
                        ├──── (1) AlyaAudio    (1:1)
                        ├────< (N) AlyaVideo   (1:N, one per render)
                        └────< (N) AlignmentRun (1:N, one per alignment attempt)
```

## Retained Models (Not Stored in DB)

- **Pasuk** — Used transiently during text fetching from Sefaria
- **AliyahRange** — Configuration model loaded from `data/aliyah_ranges.toml`
- **HebrewTextSource** — Protocol interface for text retrieval
- **VerseTimestamp** — Embedded in AlignmentRun.timestamps_json as JSON

## Deleted Models

- **Parasha** — Replaced by Playlist
- **Aliyah** — Replaced by Alya
- **AudioSource** — Replaced by AlyaAudio
- **SynchronizedVideo** — Replaced by AlyaVideo
- **TimestampMap** — Replaced by AlignmentRun

## Correction Extensions (from original spec-002)

Manual correction metadata is now embedded directly in AlignmentRun rather than
as a separate CorrectionMetadata model:

- `manual_corrections` — count of corrections
- `manually_corrected` — whether this run has been manually corrected
- `corrected_at` — when last correction was applied
- `backup_path` — path to backup of original alignment
- `original_quality` — alignment quality before corrections

The **ValidationResult** and **Violation** models remain as transient Pydantic
models used by the TimestampValidator service (not stored in DB).

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
├── db.py                # Connection manager + schema
├── playlist_repo.py     # PlaylistRepository
├── alya_repo.py         # AlyaRepository
├── alya_audio_repo.py   # AlyaAudioRepository
├── alya_video_repo.py   # AlyaVideoRepository
└── alignment_repo.py    # AlignmentRunRepository
```

Each repository provides: `insert()`, `get_by_id()`, `list_all()`, `update()`, `delete()`.
