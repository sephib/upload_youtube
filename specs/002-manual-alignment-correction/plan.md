# Implementation Plan: Manual Alignment Correction

**Branch**: `002-manual-alignment-correction` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-manual-alignment-correction/spec.md`

## Summary

Build an interactive **marimo web app** for fine-tuning audio-text alignment in Torah parasha
videos. The app wraps **wavesurfer.js** (via `anywidget`) to display an audio waveform with
draggable verse boundary regions, alongside a verse table and range sliders for precise timestamp
adjustment. Corrections persist as extended `TimestampMap` JSON files that the pipeline
automatically detects and reuses, skipping re-alignment.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: marimo (>=0.10), anywidget (>=0.9), traitlets (>=5.0), wavesurfer.js (CDN, v7), pydantic (existing)
**Storage**: File-based (JSON for TimestampMap, CSV for bulk export/import)
**Testing**: pytest (flat functions, parametrize, contract/integration/unit)
**Target Platform**: Local macOS/Linux, served via `marimo run` (localhost)
**Project Type**: Single project (Python library + marimo app)
**Performance Goals**: Load TimestampMap + audio waveform in <5s; slider edits reflect in <100ms; save <1s
**Constraints**: Audio files up to 50MB; Hebrew RTL text with Nikkud/T'amim; offline-capable (no external APIs needed for correction)
**Scale/Scope**: Typical Aliyah has 6-20 verses; single user, local tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality First | PASS | Pydantic models, type hints, SRP services, lintok enforced |
| II. TDD | PASS | Tests written before implementation per phase |
| III. UX Consistency | PASS | marimo app follows consistent widget patterns; CLI fallback for non-GUI (FR-032) |
| IV. Performance by Design | PASS | Performance goals defined above; debounce on sliders; lazy waveform load |
| V. Library-First | PASS | Correction logic is a standalone service (`services/correction/`); marimo app is a thin UI layer |
| VI. Dependency Management (UV) | PASS | All deps via `uv add`; wavesurfer.js via CDN (no Python package) |
| VII. Observability | PASS | Structured logging in all services; validation errors are actionable |
| Python Standards | PASS | No `__init__.py`; type hints everywhere; Pydantic models; f-strings with `=` |
| AI Workflow Override | PASS | No auto pre-commit runs |

## Project Structure

### Documentation (this feature)

```text
specs/002-manual-alignment-correction/
+-- plan.md              # This file
+-- research.md          # Phase 0 output
+-- data-model.md        # Phase 1 output
+-- quickstart.md        # Phase 1 output
+-- contracts/
|   +-- cli-interface.md # CLI contract for correction commands
+-- checklists/
|   +-- requirements.md  # Existing
+-- spec.md              # Existing feature spec
```

### Source Code (repository root)

```text
src/
+-- apps/
|   +-- alignment_editor.py    # Marimo app (entry point: marimo run)
+-- widgets/
|   +-- waveform_widget.py     # WaveformWidget (anywidget + wavesurfer.js)
+-- models/
|   +-- correction.py          # CorrectionMetadata, ValidationResult, BackupRecord
|   +-- timestamp.py           # VerseTimestamp (extended with original_* fields)
|   +-- timestamp_map.py       # TimestampMap (extended with correction_metadata)
+-- services/
|   +-- correction/
|   |   +-- editor.py          # CorrectionEditor (load, edit, validate, save)
|   |   +-- backup.py          # BackupManager (create, list, restore)
|   |   +-- csv_handler.py     # CSV export/import with UTF-8 Hebrew
|   |   +-- validator.py       # TimestampValidator (constraint checking)
|   +-- alignment/
|   |   +-- engine.py          # Existing (no changes)
|   +-- pipeline.py            # Extended: detect corrected timestamps
+-- cli/
|   +-- main.py                # Extended: add correction subcommands
+-- lib/
|   +-- ...                    # Existing (no changes)

tests/
+-- contract/
|   +-- test_correction_contracts.py   # API contract tests
+-- integration/
|   +-- test_correction_pipeline.py    # Pipeline integration with corrections
|   +-- test_csv_roundtrip.py          # CSV export/import fidelity
+-- unit/
|   +-- test_correction_editor.py      # CorrectionEditor unit tests
|   +-- test_correction_validator.py   # Validator unit tests
|   +-- test_backup_manager.py         # BackupManager unit tests
|   +-- test_correction_metadata.py    # Model unit tests
|   +-- test_waveform_widget.py        # Widget state sync tests
```

**Structure Decision**: Single project structure. The marimo app (`src/apps/`) is a thin UI
layer over the library services (`src/services/correction/`). All correction logic is
independently testable without marimo. The `anywidget` (`src/widgets/`) bridges Python state
to wavesurfer.js.

## Architecture: Marimo Alignment Editor App

### App Layout

```
+------------------------------------------------------------------+
|                    Marimo App: Alignment Editor                    |
+------------------------------------------------------------------+
|  SIDEBAR                |  MAIN PANEL                             |
|                         |                                         |
|  [Load TimestampMap]    |  +------------------------------------+ |
|  File: ___________      |  |  WAVEFORM PANEL (wavesurfer.js)    | |
|                         |  |                                    | |
|  Parasha: Haazinu       |  |  ~~~/\~~~~~/\/\~~~~/\~~~~~/\~~~~   | |
|  Aliyah:  Rishon        |  |  | R1  | R2  | R3  | R4 | R5 |    | |
|  Quality: 0.87          |  |  [ Regions = verse boundaries ]    | |
|  Verses:  8             |  |                                    | |
|                         |  |  [>] [||] 00:04.2 / 00:25.0       | |
|  [Save Corrections]    |  +------------------------------------+ |
|  [Export CSV]           |                                         |
|  [Restore Backup]      |  +------------------------------------+ |
|                         |  |  VIDEO PREVIEW (mo.video)           | |
|  Validation Status:     |  |  +------------------------------+  | |
|  [x] Monotonic          |  |  |  (1) verse text (gold)       |  | |
|  [x] No overlaps        |  |  |  (2) verse text (white)      |  | |
|  [x] No large gaps      |  |  +------------------------------+  | |
|  [ ] Min confidence     |  +------------------------------------+ |
|                         |                                         |
+-------------------------+  +------------------------------------+ |
                          |  |  VERSE TABLE (mo.ui.table)          | |
                          |  |  # | Reference  | Start | End | C  | |
                          |  |  1 | Deut 32:1  | 0.00  |4.20|.95 | |
                          |  |  2 | Deut 32:2  | 4.20  |7.80|.91 | |
                          |  |  3 | Deut 32:3  | 7.80  |11.5|.72 | |
                          |  +------------------------------------+ |
                          |                                         |
                          |  +------------------------------------+ |
                          |  |  ADJUSTMENT PANEL (selected verse)  | |
                          |  |  Verse 3 (Deut 32:3) Conf: 0.72    | |
                          |  |  Start: [====o==========] 7.80s    | |
                          |  |  End:   [========o======] 11.50s   | |
                          |  |  [Play Verse] [Play +-2s Context]  | |
                          |  +------------------------------------+ |
                          +------------------------------------------+
```

### Component Technology Mapping

| UI Component | marimo Widget | Purpose |
|-------------|--------------|---------|
| Waveform + regions | `mo.ui.anywidget(WaveformWidget)` | Audio visualization with draggable verse regions |
| Video preview | `mo.video(path)` | Side-by-side rendered video preview |
| Verse table | `mo.ui.table(df, selection="single")` | Click-to-navigate verse list |
| Time adjustment | `mo.ui.range_slider(step=0.05, debounce=True)` | Fine-tune start/end per verse (50ms precision) |
| Play buttons | `mo.ui.button()` | Play verse, play context |
| File loader | `mo.ui.file_browser()` | Select TimestampMap JSON |
| Save/Export | `mo.ui.button()` + `mo.download()` | Save corrections, export CSV |
| Validation | `mo.callout(kind=...)` | Real-time constraint check display |
| Layout | `mo.sidebar()` + `mo.vstack()` + `mo.hstack()` | Multi-panel composition |

### WaveformWidget (anywidget + wavesurfer.js)

Custom widget wrapping wavesurfer.js with the **Regions** and **Timeline** plugins.

**Python-JS state sync via traitlets:**

| Trait | Type | Direction | Purpose |
|-------|------|-----------|---------|
| `audio_url` | `Unicode` | Py -> JS | Audio file data URL |
| `regions` | `List[Dict]` | Py <-> JS | `[{id, start, end, color, label}]` per verse |
| `current_time` | `Float` | Py <-> JS | Playback head position (seconds) |
| `is_playing` | `Bool` | Py <-> JS | Playback state |
| `zoom_level` | `Int` | Py -> JS | Pixels per second |
| `selected_region_id` | `Unicode` | Py <-> JS | Active region for editing |
| `duration` | `Float` | JS -> Py | Total audio duration |
| `play_range` | `List[Float]` | Py -> JS | `[start, end]` for isolated playback |

**JS behavior (`_esm`):**
- Initialize wavesurfer.js with Regions + Timeline plugins
- Load audio from `audio_url` trait (data URL or file path)
- Create colored regions from `regions` trait
- On region drag-end: update `regions` trait, `model.save_changes()`
- On region click: set `selected_region_id`, seek to region start
- On `change:play_range`: play audio segment between `[start, end]`
- Periodically sync `current_time` during playback

**Region color scheme:**

| State | Color | Meaning |
|-------|-------|---------|
| Normal (confidence >= 0.85) | `rgba(100, 149, 237, 0.3)` | Cornflower blue |
| Low confidence (< 0.85) | `rgba(255, 165, 0, 0.4)` | Orange warning |
| Selected/Active | `rgba(255, 215, 0, 0.5)` | Gold, prominent |
| Corrected | `rgba(50, 205, 50, 0.3)` | Green, confirmed |

### Reactive Data Flow

```
User clicks verse row in table
    |
    +---> selected_verse_idx updates (marimo reactivity)
    +---> Waveform seeks to verse.start_time
    +---> Range slider value = [start_time, end_time]
    +---> Waveform region highlighted (gold)
    +---> Adjustment panel shows verse details

User drags range slider handles
    |
    +---> verse_timestamps[idx].start_time / end_time updates
    +---> Waveform region boundaries move
    +---> Table row times update
    +---> Validation runs (all constraints)
    +---> Validation callouts update

User drags region on waveform (wavesurfer Regions)
    |
    +---> anywidget syncs region bounds to Python (traitlets)
    +---> Range slider values update
    +---> Same cascade as slider drag

User clicks [Play Verse]
    |
    +---> play_range = [start_time, end_time]
    +---> Wavesurfer plays isolated audio segment

User clicks [Save Corrections]
    |
    +---> BackupManager.create_backup(original)
    +---> CorrectionEditor.save(timestamp_map, metadata)
    +---> Success callout displayed
```

### Marimo Cell Structure

| Cell | Name | Purpose | Depends On |
|------|------|---------|------------|
| 1 | `imports` | Import marimo, models, services | - |
| 2 | `file_loader` | `mo.ui.file_browser()` for TimestampMap JSON | - |
| 3 | `load_data` | Parse JSON into TimestampMap + DataFrame | `file_loader` |
| 4 | `state` | `mo.state()` for mutable correction state + undo stack | `load_data` |
| 5 | `waveform` | `mo.ui.anywidget(WaveformWidget)` | `state` |
| 6 | `verse_table` | `mo.ui.table(df, selection="single")` | `state` |
| 7 | `selected_verse` | Extract selection from table + waveform | `verse_table`, `waveform` |
| 8 | `adjustment` | Range slider + play buttons | `selected_verse` |
| 9 | `apply_edit` | Apply slider/region changes to state | `adjustment`, `waveform` |
| 10 | `validation` | Run constraints, display callouts | `state` |
| 11 | `video_preview` | `mo.video()` panel | `load_data` |
| 12 | `sidebar` | Save/export/restore buttons + metadata | `state`, `validation` |
| 13 | `layout` | `mo.sidebar() + mo.vstack() + mo.hstack()` | all cells |

## Implementation Phases

### Phase 1: Core Library (P1 - US1, US3)

Focus: Correction logic as testable library, no UI yet.

1. **CorrectionMetadata model** — `src/models/correction.py`
2. **TimestampMap extension** — add `correction_metadata` field
3. **VerseTimestamp extension** — add `original_start_time`, `original_end_time`, `manually_corrected`
4. **TimestampValidator** — constraint checking service (extracted from model validator)
5. **BackupManager** — create/list/restore backups
6. **CorrectionEditor** — load, edit single verse, validate, save with backup
7. **Pipeline integration** — detect `manually_corrected`, skip alignment, `--force-realign` flag
8. **CLI subcommands** — `correction show`, `correction edit`, `correction restore`

### Phase 2: Interactive App (P1 - US1 visual)

Focus: Marimo app with waveform and interactive editing.

9. **WaveformWidget** — anywidget wrapping wavesurfer.js + Regions + Timeline
10. **Marimo app cells** — file loader, waveform, table, sliders, validation, save
11. **App layout** — sidebar + main panel composition
12. **Play controls** — play verse, play context (+/-2s)

### Phase 3: Productivity (P2 - US2, US4)

13. **CSV export/import** — `mo.download()` for export, `mo.ui.file()` for import
14. **Confidence indicators** — color-coded table rows, orange waveform regions
15. **Jump to next low-confidence** — navigation helper
16. **Video preview panel** — re-render short preview with corrected timestamps

### Phase 4: Safety (P3 - US5)

17. **Backup list UI** — sidebar panel listing all backups with restore buttons
18. **Undo/redo stack** — `mo.state()` with history for in-session undo

## Dependencies (new)

```toml
# pyproject.toml additions
[project.dependencies]
marimo = ">=0.10"
anywidget = ">=0.9"
traitlets = ">=5.0"
```

wavesurfer.js v7 loaded via CDN in the anywidget `_esm` module (no Python package).

## Complexity Tracking

> No constitution violations detected. All principles pass.

| Consideration | Decision | Rationale |
|--------------|----------|-----------|
| anywidget vs mo.iframe | anywidget | Proper bidirectional state sync; iframe requires postMessage hacks |
| wavesurfer.js via CDN vs npm bundle | CDN | No frontend build tooling needed; simpler for Python-only project |
| mo.state() for undo | Lightweight list-based stack | No external state management library needed |
| Validation in model vs service | Both | Model validates on construction (Pydantic); service validates incrementally for UI feedback |
