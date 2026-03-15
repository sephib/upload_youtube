# Torah Sync - Automated Torah Reading Audio-Visual Synchronization

**Status**: 🚧 In Development
**Version**: 0.1.0
**Python**: 3.13+

## Overview

Torah Sync generates synchronized videos from Torah reading audio files, where Hebrew text with vowels and cantillation marks highlights in real-time as each verse is recited.

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

```bash
# Process a single audio file
uv run torah-sync "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"

# Batch process all audio files
uv run torah-sync batch data/audio/
```

## Architecture

- **Database**: DuckDB (embedded) with 7 tables: `playlists`, `alyot`, `alya_ranges`, `alya_audio`, `alya_videos`, `alignment_runs`, `pasuk_alignments`
- **Alignment**: aeneas (forced alignment) produces per-verse `PasukAlignment` records
- **Text**: Sefaria API for Hebrew text with vowels and cantillation marks
- **Video**: moviepy renders highlighted text synchronized to audio

## Documentation

- [Audio-Text Sync Spec](specs/001-torah-audio-text-sync/spec.md)
- [Audio-Text Sync Plan](specs/001-torah-audio-text-sync/plan.md)
- [Manual Alignment Correction Spec](specs/002-manual-alignment-correction/spec.md)
- [Manual Alignment Correction Plan](specs/002-manual-alignment-correction/plan.md)
- [Data Model (ERD)](tmp/db_erd.md)

**Edited by Claude Code**
