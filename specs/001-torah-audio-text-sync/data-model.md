# Data Model: Automated Torah Reading Audio-Visual Synchronization

<!-- Edited by Claude Opus 4.6 -->

**Date**: 2026-03-15
**Feature**: 001-torah-audio-text-sync
**Purpose**: Define core entities and their relationships for Torah audio-text synchronization
**Source of truth**: `tmp/db_erd.md` (ERD v2)

## Overview

All entities are flat, DuckDB-storable models using a repository pattern for persistence.
See `specs/002-manual-alignment-correction/data-model.md` for full entity definitions
including per-pasuk alignment and correction tracking.

## Entity Definitions

### Playlist (replaces Parasha)

Represents a YouTube playlist for a weekly Torah portion.

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
| youtube_playlist_id | VARCHAR   | NULLABLE                  |
| created_at          | TIMESTAMP | NOT NULL, DEFAULT now()   |

### Alya (replaces Aliyah)

Core processing unit — one Aliyah within a Parasha. Haftara is stored as `order_num=9`,
maftir as `order_num=8`.

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

**State transitions**:
- `pending` → Audio file identified, not yet processed
- `aligning` → Forced alignment in progress
- `aligned` → Timestamps generated successfully
- `rendering` → Video generation in progress
- `completed` → Video output ready
- `failed` → Processing error occurred

### AlyaRange (replaces AliyahRange config)

Verse range for an alya. Torah aliyot have one range; Haftarot may have
multiple non-consecutive ranges (compound readings).

**Table**: `alya_ranges`

| Column        | Type      | Constraints                    |
|---------------|-----------|--------------------------------|
| id            | INTEGER   | PK, auto-increment             |
| alya_id       | INTEGER   | FK → alyot.id, NOT NULL        |
| range_order   | INTEGER   | NOT NULL, 1-based              |
| book          | VARCHAR   | NOT NULL                       |
| chapter_start | INTEGER   | NOT NULL, > 0                  |
| verse_start   | INTEGER   | NOT NULL, > 0                  |
| chapter_end   | INTEGER   | NOT NULL, > 0                  |
| verse_end     | INTEGER   | NOT NULL, > 0                  |
| created_at    | TIMESTAMP | NOT NULL, DEFAULT now()        |

**Unique**: (alya_id, range_order)

### AlyaAudio (replaces AudioSource)

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

### AlyaVideo (replaces SynchronizedVideo)

Rendered video file for an Alya. One-to-one with Alya.

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
| youtube_video_id | VARCHAR   | NULLABLE                          |
| created_at       | TIMESTAMP | NOT NULL, DEFAULT now()           |

### AlignmentRun (replaces TimestampMap)

Result of a forced alignment run. Links to `alya_audio` (the source audio).

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

### PasukAlignment (replaces VerseTimestamp embedded in JSON)

Individual verse alignment within an alignment run. Replaces the `timestamps_json`
blob with per-verse rows for SQL queries and individual correction tracking.

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

### Pasuk (Verse) — transient model

Used transiently during text fetching from Sefaria, not stored in DB.

**Fields**:
- `reference: str` - Canonical verse reference (e.g., "Deuteronomy 32:1")
- `book: str` - Book name
- `chapter: int` - Chapter number (> 0)
- `verse: int` - Verse number (> 0)
- `hebrew_text: str` - Hebrew text with Nikkud and T'amim

### HebrewTextSource — protocol

Protocol interface for text retrieval (Sefaria API).

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
                        └──── (1) AlyaVideo      (1:1)
```

See `tmp/db_erd.md` for the full Mermaid ERD.

## Text Fetching Architecture

**Component Hierarchy**:

```text
ProcessingPipeline
    │
    ├─> ParashaTextFetcher (batch retrieval, Aliyah-aware)
    │       │
    │       └─> SefariaClient (low-level API wrapper)
    │               │
    │               └─> CachedSefariaClient (caching layer)
    │
    └─> (alternative) SefariaClient (direct per-verse fallback)
```

The text fetcher makes one Sefaria API call per `alya_ranges` row and concatenates
the results. Both Torah and Haftara use the same `book chapter:verse` API format.

**Sefaria API notes**:
- Torah verses: `Deuteronomy 32:1-6` → flat array of verse strings
- Haftara verses: `II Samuel 22:1-51` → identical structure
- Cross-chapter: `I Kings 18:46-19:21` → `isSpanning: true`, `spanningRefs` breaks into parts
- Both use `sectionNames: ["Chapter", "Verse"]`, `addressTypes: ["Perek", "Pasuk"]`

## Key Design Decisions

1. **Flat DuckDB entities** — No nested Pydantic composition; FK relationships via repository pattern
2. **Per-pasuk alignment** — Individual verse rows instead of JSON blob enables SQL queries and per-verse correction
3. **Audio as alignment source** — `alignment_runs` links to `alya_audio` because the audio file is the input to the alignment engine
4. **Haftara as aliyah** — `order_num=9`, same pipeline, no separate entity
5. **Compound ranges** — `alya_ranges` supports non-consecutive Haftarot readings
6. **State machine** — Alya state transitions tracked for pipeline monitoring
