# CLI Interface Contract: Manual Alignment Correction

<!-- Edited by Claude Opus 4.6 -->

**Date**: 2026-03-15
**Purpose**: Define CLI subcommands for manual alignment correction
**Source of truth**: `tmp/db_erd.md` (ERD v2)

## Command Group: `torah-sync correction`

**Description**: Subcommands for reviewing, correcting, and managing verse-audio alignment timestamps.
Data is stored in DuckDB (`alignment_runs` + `pasuk_alignments` tables).

### Synopsis

```bash
uv run torah-sync correction show ALIGNMENT_RUN_ID
uv run torah-sync correction edit ALIGNMENT_RUN_ID
uv run torah-sync correction export ALIGNMENT_RUN_ID [--output CSV_FILE]
uv run torah-sync correction import ALIGNMENT_RUN_ID CSV_FILE
uv run torah-sync correction backup list ALIGNMENT_RUN_ID
uv run torah-sync correction backup restore ALIGNMENT_RUN_ID BACKUP_FILE
uv run torah-sync correction app [ALIGNMENT_RUN_ID]
```

---

### `correction show`

**Description**: Display an AlignmentRun with its PasukAlignments in human-readable format.

**Arguments**:
- `ALIGNMENT_RUN_ID` (required) - ID of the alignment run in DuckDB

**Options**:
- `--json` - Output as formatted JSON instead of table
- `--low-confidence` - Only show verses with confidence < 0.85

**Output**:
```text
AlignmentRun #42: האזינו / ראשון
Quality: 0.87 | Verses: 8 | Corrected: No
Audio: data/audio/haazinu_rishon.wav (25.0s)

 #  Reference         Start    End     Dur    Conf   Status
 1  Deuteronomy 32:1   0.00    4.20   4.20   0.95   OK
 2  Deuteronomy 32:2   4.20    7.80   3.60   0.91   OK
 3  Deuteronomy 32:3   7.80   11.50   3.70   0.72   [!] LOW
 4  Deuteronomy 32:4  11.50   15.20   3.70   0.88   OK
 ...

[!] 1 verse(s) below confidence threshold (0.85)
```

**Exit Codes**:
- `0` - Success
- `1` - AlignmentRun not found in DuckDB
- `2` - Database error

---

### `correction edit`

**Description**: Edit a single verse timestamp via CLI prompts. Updates `pasuk_alignments` rows.

**Arguments**:
- `ALIGNMENT_RUN_ID` (required) - ID of the alignment run in DuckDB

**Options**:
- `--verse N` - Verse number to edit (1-indexed). If omitted, prompts interactively.
- `--start SECONDS` - New start time
- `--end SECONDS` - New end time
- `--auto-adjust` - Automatically adjust adjacent verse boundaries (default: True)
- `--no-auto-adjust` - Disable adjacent verse auto-adjustment

**Example**:
```bash
# Edit verse 3 directly
uv run torah-sync correction edit 42 --verse 3 --start 7.60 --end 11.80

# Interactive mode
uv run torah-sync correction edit 42
```

**Behavior**:
- Before first edit, saves `original_start_time`/`original_end_time` on the PasukAlignment row
- Sets `pasuk_alignments.manually_corrected = true` on edited verse
- Sets `alignment_runs.manually_corrected = true` and `corrected_at` on the run

**Exit Codes**:
- `0` - Correction saved successfully
- `1` - AlignmentRun not found
- `2` - Validation failed (with error details on stderr)

---

### `correction export`

**Description**: Export PasukAlignments to CSV for bulk editing in a spreadsheet.

**Arguments**:
- `ALIGNMENT_RUN_ID` (required) - ID of the alignment run in DuckDB

**Options**:
- `--output CSV_FILE` - Output CSV path (default: `alignment_run_{id}.csv`)

**Output CSV format**:
```csv
reference,hebrew_text,start_time,end_time,confidence
Deuteronomy 32:1,האזינו השמים ואדברה,0.00,4.20,0.95
Deuteronomy 32:2,יערף כמטר לקחי,4.20,7.80,0.91
```

**Exit Codes**:
- `0` - Export successful
- `1` - AlignmentRun not found

---

### `correction import`

**Description**: Import corrected timestamps from a CSV file into DuckDB.

**Arguments**:
- `ALIGNMENT_RUN_ID` (required) - ID of the alignment run to update
- `CSV_FILE` (required) - Path to CSV file with corrected timestamps

**Options**:
- `--dry-run` - Validate without saving (show what would change)
- `--force` - Skip confirmation prompt

**Exit Codes**:
- `0` - Import successful
- `1` - File error
- `2` - Validation failed (lists all violations)
- `3` - Verse count mismatch

---

### `correction backup list`

**Description**: List available backups for an AlignmentRun.

**Arguments**:
- `ALIGNMENT_RUN_ID` (required) - ID of the alignment run

**Output**:
```text
Backups for: AlignmentRun #42 (האזינו / ראשון)

 #  Created              Description           Path
 1  2026-03-10 14:30:00  original_automated     backups/alignment_42.original.json
 2  2026-03-11 10:15:00  manual_correction      backups/alignment_42.2026-03-11T10-15-00.json
```

---

### `correction backup restore`

**Description**: Restore an AlignmentRun from a backup file.

**Arguments**:
- `ALIGNMENT_RUN_ID` (required) - ID of the alignment run to restore
- `BACKUP_FILE` (required) - Path to backup file to restore from

**Options**:
- `--force` - Skip confirmation prompt

**Exit Codes**:
- `0` - Restore successful
- `1` - File error
- `2` - Backup schema incompatible

---

### `correction app`

**Description**: Launch the interactive marimo alignment editor.

**Arguments**:
- `ALIGNMENT_RUN_ID` (optional) - ID of the alignment run (can also be selected in the app)

**Options**:
- `--port PORT` - Port for marimo web server (default: 2718)
- `--host HOST` - Host to bind to (default: localhost)
- `--headless` - Don't open browser automatically

**Example**:
```bash
# Launch editor with a specific alignment run
uv run torah-sync correction app 42

# Launch editor (select in UI)
uv run torah-sync correction app
```

**Exit Codes**:
- `0` - App closed normally
- `1` - marimo not installed or failed to start

---

## Extended: `torah-sync` (main command)

### New Option: `--force-realign`

Added to the main `torah-sync` processing command:

```bash
uv run torah-sync --force-realign AUDIO_FILE
```

**Behavior**:
- When set, pipeline ignores existing corrected AlignmentRun
- Creates a backup of the corrected version before overwriting
- Warns user: "Overwriting manually corrected alignment for {parasha}/{aliyah}"

### Modified Pipeline Behavior

Without `--force-realign`:
1. Pipeline queries DuckDB for existing AlignmentRun for the alya's audio
2. If found AND `manually_corrected is True`:
   - Log: "Using manually corrected alignment, skipping re-alignment"
   - Skip Stage 5 (alignment)
   - Proceed to Stage 6 (rendering) with corrected PasukAlignments
3. If found but NOT manually corrected: re-run alignment as normal
4. If not found: run alignment as normal

## Error Message Standards

All error messages follow the pattern from spec FR-031:

```text
[CONSTRAINT_TYPE] Verse {reference}: {description}
```

Examples:
- `[OVERLAP] Verse Deut 32:2: end_time (9.0s) overlaps with Deut 32:3 start_time (8.5s)`
- `[DURATION] Verse Deut 32:3: duration must be > 0 seconds (start=7.80, end=7.80)`
- `[MONOTONIC] Verse Deut 32:4: start_time (10.0s) not after Deut 32:3 end_time (11.5s)`
- `[GAP] Warning: gap of 7.2s between Deut 32:3 and Deut 32:4 — verify this is intentional`
