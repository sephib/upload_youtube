# Torah Sync - Automated Torah Reading Audio-Visual Synchronization

**Status**: 🚧 In Development
**Version**: 0.1.0
**Python**: 3.13+

## Overview

Torah Sync generates synchronized videos from Torah reading audio files, where Hebrew text with vowels and cantillation marks highlights in real-time as each verse is recited. Supports both weekly Torah portions (Parashot) and Megillot (שיר השירים, רות, איכה, קהלת, אסתר).

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- System dependencies (macOS): `brew install espeak ffmpeg`

### Installation

```bash
# Install Python dependencies (includes aeneas from vendored patched fork)
LDFLAGS="-L/opt/homebrew/opt/espeak/lib" CPPFLAGS="-I/opt/homebrew/opt/espeak/include" uv sync

# Verify aeneas installation
uv run python -m aeneas.diagnostics

# Download Hebrew font
mkdir -p fonts
curl -L "https://github.com/google/fonts/raw/main/ofl/frankruhl/FrankRuhl-Regular.ttf" \
  -o fonts/FrankRuhl-Regular.ttf
```

> **Note**: aeneas is vendored at `vendor/aeneas/` from the [avinashvarna/aeneas](https://github.com/avinashvarna/aeneas/tree/py312_support) fork (Python 3.12+ support). The Festival TTS extension (`cfw`) is excluded from the build since it requires additional system libraries. The `LDFLAGS`/`CPPFLAGS` are needed so the C extensions can find Homebrew's espeak headers on Apple Silicon.

### Basic Usage

#### Legacy: Single-Step Processing

```bash
# Process a single audio file (align + render in one step)
uv run torah-sync process "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"
```

#### Modern: Three-Phase Pipeline

For better control and manual correction capability:

```bash
# Phase 1a: Align a Torah audio file (parses filename)
uv run torah-sync align "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"

# Phase 1b: Align an entire playlist (parasha or megillah)
uv run torah-sync align-playlist "שיר השירים"
uv run torah-sync align-playlist "האזינו"

# Phase 1c: Align a single pre-ingested alya by DB id
uv run torah-sync align-alya 487

# Phase 2: (Optional) Manual correction
uv run torah-sync correct 1  # Opens marimo app

# Phase 3: Render video
uv run torah-sync render 1

# Phase 3b: Render all alyot/chapters of a playlist
uv run torah-sync render-playlist "שיר השירים"
```

#### Megillot Workflow

For megillot (scrolls), audio files are ingested separately:

```bash
# Step 1: Rename MP3 files to match JPG thumbnails
uv run python scripts/rename_megillot_audio.py "data/torah_read/מגילות/שיר השירים" --apply

# Or rename all megillot at once
uv run python scripts/rename_megillot_audio.py "data/torah_read/מגילות" --all --apply

# Step 2: Ingest into DuckDB (creates playlist, alyot, audio records)
uv run python scripts/ingest_megillah.py "שיר השירים" "Song of Songs" \
    "data/torah_read/מגילות/שיר השירים"

# Step 3: Align all chapters
uv run torah-sync align-playlist "שיר השירים"

# Step 4: (Optional) Manual correction
uv run torah-sync correct

# Step 5: Render all chapters
uv run torah-sync render-playlist "שיר השירים"
```

## Manual Alignment Correction

After running the alignment phase, you may want to manually correct timing issues using the interactive marimo app.

### Launch the Alignment Editor

```bash
# Via CLI wrapper (recommended)
uv run torah-sync correct 1

# Or directly with marimo
uv run marimo edit src/apps/alignment_editor.py --watch
```

The `--watch` flag auto-reloads the app when code changes.

### Using the Editor

The marimo app provides:

- **WaveSurfer.js integration**: Visual waveform with playback controls
- **Verse-by-verse editing**: Adjust start/end times for each pasuk
- **Real-time preview**: Hear changes immediately
- **CSV export/import**: Bulk editing via spreadsheet
- **Quality metrics**: Alignment confidence scores

**Workflow**:
1. Select the alya from the dropdown
2. Play the audio and identify mistimed verses
3. Adjust timestamps using the interactive controls
4. Save changes to the database
5. Proceed to Phase 3 (rendering)

**Export for bulk editing**:
```bash
# From the marimo app, use the CSV export button
# Edit in spreadsheet software
# Import back via the CSV import button
```

## Video Rendering

### Check Alignment Status

Before rendering, check which alyot are available:

```bash
uv run torah-sync status
```

Output example:
```
📖 האזינו (Deuteronomy)
  ✅ ראשון (id=1, state=aligned quality=0.95 [corrected])
  ✅ שני (id=2, state=aligned quality=0.92)
  ✅ שלישי (id=3, state=aligned quality=0.94)
  ...
```

### Render Single Alya

Generate a video for one aliyah:

```bash
# Render video for alya ID 1
uv run torah-sync render 1

# Specify custom output directory
uv run torah-sync render 1 --output ./my-videos/
```

**Output**: `output/videos/האזינו_ראשון_sync.mp4`

**Video Features**:
- **Resolution**: 1280×720 (720p HD)
- **Frame Rate**: 30 FPS
- **Highlighting**: Karaoke-style verse-by-verse in gold
- **Scrolling**: Auto-enabled for 7+ verses
- **Hebrew Text**: Full nikkud (vowels) and te'amim (cantillation marks)

### Render Entire Playlist

To render all alyot/chapters for a parasha or megillah:

**Method 1: CLI Command (Recommended)**

```bash
# Render all alyot for a parasha
uv run torah-sync render-playlist האזינו

# Render all chapters of a megillah
uv run torah-sync render-playlist "שיר השירים"

# With custom output directory
uv run torah-sync render-playlist האזינו --output ./my-videos/
```

This automatically finds the playlist, renders all alyot/chapters sequentially, and provides a summary report.

**Method 2: Manual Sequential Rendering**

```bash
# Get the list of alya IDs
uv run torah-sync status

# Render each alya
uv run torah-sync render 1
uv run torah-sync render 2
uv run torah-sync render 3
# ... continue for all alyot
```

**Method 3: Bash Loop (Sequential IDs)**

If your alyot have sequential IDs (e.g., 1-7 for Ha'azinu):

```bash
# Render alyot 1 through 7
for alya_id in {1..7}; do
  echo "Rendering alya $alya_id..."
  uv run torah-sync render $alya_id
done
```

**Method 4: Extract IDs from Status**

For non-sequential IDs, extract them from status output:

```bash
# Render all alyot for Ha'azinu parasha
uv run torah-sync status | \
  grep "📖 האזינו" -A 10 | \
  grep -oE "id=[0-9]+" | \
  cut -d= -f2 | \
  xargs -I {} sh -c 'echo "Rendering alya {}..." && uv run torah-sync render {}'
```

### Troubleshooting

**Database Lock Error**:
```
Error: Could not set lock on file "data/torah_sync.duckdb"
```

**Solution**: Close the marimo alignment editor before rendering:
```bash
# Kill marimo processes
pkill -f marimo

# Then retry rendering
uv run torah-sync render 1
```

**Missing Alignment Data**:
```
Error: No alignment run found
```

**Solution**: Run the alignment phase first:
```bash
# For Torah audio (parses filename)
uv run torah-sync align "data/audio/file.mp4"

# For megillot / pre-ingested audio
uv run torah-sync align-playlist "שיר השירים"
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `torah-sync align <file>` | Align a Torah audio file (parses Hebrew filename) |
| `torah-sync align-playlist <name>` | Align all alyot/chapters of a parasha or megillah |
| `torah-sync align-alya <id>` | Align a single pre-ingested alya by DB id |
| `torah-sync correct [id]` | Launch marimo alignment editor |
| `torah-sync render <id>` | Render video for a single alya |
| `torah-sync render-playlist <name>` | Render all alyot/chapters of a playlist |
| `torah-sync status` | Show alignment status for all playlists |
| `torah-sync evaluate` | Evaluate alignment accuracy |
| `torah-sync process <file>` | Legacy: align + render in one step |

## Architecture

- **Database**: DuckDB (embedded) with 7 tables: `playlists`, `alyot`, `alya_ranges`, `alya_audio`, `alya_videos`, `alignment_runs`, `pasuk_alignments`
- **Alignment**: aeneas (forced alignment) produces per-verse `PasukAlignment` records
- **Text**: Sefaria API for Hebrew text with vowels and cantillation marks
- **Video**: moviepy renders highlighted text synchronized to audio
  - **Dual-layer rendering**: White text (always visible) + Gold highlight (timed per verse)
  - **Auto-scrolling**: Enabled for 7+ verses to keep current verse visible
  - **Verse-level highlighting**: Karaoke-style gold highlighting synced to audio timestamps

## Documentation

- [Audio-Text Sync Spec](specs/001-torah-audio-text-sync/spec.md)
- [Audio-Text Sync Plan](specs/001-torah-audio-text-sync/plan.md)
- [Manual Alignment Correction Spec](specs/002-manual-alignment-correction/spec.md)
- [Manual Alignment Correction Plan](specs/002-manual-alignment-correction/plan.md)
- [Data Model (ERD)](tmp/db_erd.md)

**Edited by Claude Code**
