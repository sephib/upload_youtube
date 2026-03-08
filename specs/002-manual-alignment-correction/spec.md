# Feature Specification: Manual Alignment Correction

**Feature Branch**: `002-manual-alignment-correction`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "add a module to allow for human in the loop to update the alignment when there is fine tuning required"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct Misaligned Verse Boundaries (Priority: P1)

As a Torah educator preparing synchronized videos, when the automated alignment system (aeneas) produces inaccurate verse boundaries (e.g., splits a single verse into two segments or merges two verses), I want to manually review and correct the timestamps so that the final video has accurate synchronization.

**Why this priority**: This is the core value of the feature. Without the ability to correct alignment errors, videos with poor automated alignment cannot be used, rendering the entire system unreliable for production use.

**Independent Test**: Can be fully tested by providing a TimestampMap JSON file with known incorrect timestamps, allowing the user to edit specific verse start/end times, validating the edits maintain constraints, and saving the corrected version. Delivers immediate value by making previously unusable alignments production-ready.

**Acceptance Scenarios**:

1. **Given** a TimestampMap JSON file with verse 3 incorrectly ending at 12.3s (should be 11.8s), **When** user loads the file for correction and adjusts verse 3 end time to 11.8s, **Then** the system validates the change, auto-adjusts verse 4 start time to 11.8s to maintain continuity, and saves the corrected timestamps with a backup of the original
2. **Given** a TimestampMap with low confidence score (0.72) on verse 5, **When** user reviews the timestamps, **Then** the system highlights low-confidence verses and allows targeted correction
3. **Given** user attempts to set verse 2 end time to 9.0s when verse 3 starts at 8.5s, **When** user saves the change, **Then** the system rejects the edit with error "Verse 2 end time (9.0s) overlaps with verse 3 start time (8.5s)" and provides guidance

---

### User Story 2 - Bulk Timestamp Editing via CSV (Priority: P2)

As a Torah educator with many verses to correct, when I need to adjust multiple timestamps efficiently, I want to export the TimestampMap to CSV format, edit it in a spreadsheet tool (Excel, Google Sheets), and import the corrected version so that I can make bulk edits faster than one-by-one corrections.

**Why this priority**: Enables efficient workflows for users comfortable with spreadsheets. Not critical for MVP (can correct verse-by-verse), but significantly improves productivity for power users.

**Independent Test**: Can be fully tested by exporting a TimestampMap to CSV, verifying all data is present (reference, hebrew_text, start_time, end_time, confidence), editing the CSV externally, importing it back, and validating all constraints are enforced. Delivers value by enabling batch operations.

**Acceptance Scenarios**:

1. **Given** a TimestampMap JSON file with 8 verses, **When** user exports to CSV format, **Then** the system creates a CSV file with columns: reference, hebrew_text, start_time, end_time, confidence, with UTF-8 encoding preserved for Hebrew text
2. **Given** a CSV file edited to change 3 verse timestamps, **When** user imports the CSV, **Then** the system validates all edits (monotonic ordering, no overlaps, no gaps >5s) and reports any constraint violations before allowing import
3. **Given** a CSV with invalid data (verse 4 start time = 10.0s, verse 5 start time = 9.5s - non-monotonic), **When** user imports, **Then** the system rejects the import with error "Timestamps not monotonically increasing: verse 4 ends at 10.0s but verse 5 starts at 9.5s"

---

### User Story 3 - Pipeline Integration with Corrected Timestamps (Priority: P1)

As a Torah educator who has manually corrected timestamps for an Aliyah, when I re-run the processing pipeline (e.g., to regenerate video with different settings), I want the system to use my corrected timestamps instead of re-running automated alignment so that my manual corrections are preserved and not overwritten.

**Why this priority**: Critical for production workflows. Without this, users would have to re-correct timestamps every time they process the same audio, making manual correction impractical.

**Independent Test**: Can be fully tested by correcting a TimestampMap, marking it as manually corrected, re-running the pipeline on the same audio file, and verifying the pipeline skips alignment and uses the corrected timestamps directly. Delivers value by making corrections permanent.

**Acceptance Scenarios**:

1. **Given** user has corrected timestamps for "Haazinu Rishon" and saved the file, **When** user runs the pipeline on the same audio file, **Then** the system detects existing corrected timestamps, skips the alignment step, and proceeds directly to video rendering using the corrected timestamps
2. **Given** a manually corrected TimestampMap marked as "manually_corrected: true", **When** user runs pipeline with --force-realign flag, **Then** the system creates a new automated alignment (overwriting the manual corrections) and warns the user
3. **Given** user corrects timestamps and saves, **When** the pipeline runs, **Then** the system creates a backup of the original automated alignment before applying corrections

---

### User Story 4 - Review Alignment Quality Before Correction (Priority: P2)

As a Torah educator processing a new Aliyah, when automated alignment completes with low confidence scores, I want to be notified which verses need review so that I can focus my correction efforts on problematic verses rather than reviewing every verse.

**Why this priority**: Improves user efficiency by highlighting problem areas. Not critical for MVP (users can manually review all verses), but reduces correction time significantly.

**Independent Test**: Can be fully tested by processing an audio file that produces alignments with varying confidence scores (some >0.90, some <0.90), displaying the TimestampMap with confidence indicators, and allowing users to sort/filter by confidence. Delivers value by triaging correction work.

**Acceptance Scenarios**:

1. **Given** automated alignment completes with overall confidence 0.87 (below 0.90 threshold), **When** pipeline finishes, **Then** the system warns "Alignment confidence (0.87) below threshold (0.90). Manual review recommended for 3 verses with confidence <0.85"
2. **Given** a TimestampMap with 8 verses where verses 2, 5, and 7 have confidence <0.85, **When** user loads the file for correction, **Then** the system highlights these verses and allows "jump to next low-confidence verse" navigation
3. **Given** user corrects all low-confidence verses, **When** user saves, **Then** the system recalculates overall confidence and marks the TimestampMap as "manually_corrected: true"

---

### User Story 5 - Restore from Backup (Priority: P3)

As a Torah educator who accidentally made incorrect edits to a TimestampMap, when I realize my corrections were wrong, I want to restore the original automated alignment from backup so that I can start over without re-running the alignment process.

**Why this priority**: Safety net for user errors. Lower priority because it's a recovery feature (not core workflow) and users can re-run alignment if needed.

**Independent Test**: Can be fully tested by correcting a TimestampMap (which creates a backup), making additional edits that are incorrect, and restoring from the backup file to return to the original state. Delivers value by providing undo functionality.

**Acceptance Scenarios**:

1. **Given** user has corrected a TimestampMap (backup created automatically), **When** user runs restore command with the backup file path, **Then** the system replaces the current TimestampMap with the backup and marks it as "manually_corrected: false"
2. **Given** multiple backups exist (original automated + previous manual corrections), **When** user lists available backups, **Then** the system shows all backups with timestamps and descriptions (e.g., "original_automated_2026-03-08_14-30.json", "manual_correction_2026-03-08_15-45.json")

---

### Edge Cases

- What happens when user edits a verse to have zero duration (start_time = end_time)? System should reject with error "Verse must have duration >0 seconds"
- What happens when user imports a CSV with missing Hebrew text column? System should reject with error "Missing required column: hebrew_text"
- What happens when user tries to correct a TimestampMap while video is being rendered? System should detect file lock and warn "File in use by rendering process, wait for completion"
- What happens when user imports a CSV with 10 verses but original had 8 verses? System should reject with error "Verse count mismatch: expected 8 verses, found 10 in CSV"
- What happens when user corrects timestamps but audio file is missing? System should warn "Cannot validate against audio duration (file not found)" but allow save
- What happens when gap between verses exceeds 5 seconds? System should warn "Large gap detected (7.2s between verse 3 and 4) - verify this is intentional" but allow if user confirms
- What happens when user tries to restore from a backup that doesn't match current TimestampMap structure (old schema version)? System should reject with error "Backup schema incompatible, cannot restore"

## Requirements *(mandatory)*

### Functional Requirements

- **FR-020**: System MUST load existing TimestampMap JSON files for review and editing
- **FR-021**: System MUST display verse references, Hebrew text, start times, end times, and confidence scores in human-readable format
- **FR-022**: System MUST allow users to edit individual verse start and end times
- **FR-023**: System MUST validate all edits maintain constraints: timestamps are monotonically increasing, no overlaps between verses, gaps between verses are ≤5 seconds, all durations are >0
- **FR-024**: System MUST automatically create a backup of the original TimestampMap before saving any corrections
- **FR-025**: System MUST mark corrected TimestampMaps with metadata including: manually_corrected flag (true), correction timestamp, corrections count, backup file path
- **FR-026**: System MUST export TimestampMap to CSV format with columns: reference, hebrew_text, start_time, end_time, confidence
- **FR-027**: System MUST import CSV files and validate all data before applying changes (schema validation, constraint validation, UTF-8 encoding)
- **FR-028**: System MUST integrate with the processing pipeline to detect existing corrected TimestampMaps and skip automated alignment
- **FR-029**: System MUST allow users to restore TimestampMaps from backup files
- **FR-030**: System MUST preserve Hebrew text UTF-8 encoding during CSV export/import round-trips
- **FR-031**: System MUST provide clear error messages for all validation failures, specifying which constraint was violated and which verse(s) are affected
- **FR-032**: System MUST support command-line interface operations (no GUI dependencies required)
- **FR-033**: System MUST highlight low-confidence verses (confidence <0.85) when displaying TimestampMaps for correction
- **FR-034**: When user adjusts a verse end time, system MUST offer to auto-adjust the next verse start time to maintain continuity (no gaps)

### Key Entities

- **CorrectionMetadata**: Represents metadata about manual corrections including correction timestamp, username/identifier, original confidence score, count of corrections made, and backup file path
- **TimestampMap (Extended)**: Existing TimestampMap model extended with manually_corrected boolean flag and optional CorrectionMetadata
- **ValidationResult**: Represents the outcome of timestamp validation including pass/fail status, list of constraint violations with specific error messages, and affected verse references
- **BackupRecord**: Represents a backup file including file path, creation timestamp, description (e.g., "original_automated", "manual_correction_v1"), and schema version

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-010**: Users can load, correct, and save a TimestampMap with 10 verses in under 5 minutes
- **SC-011**: 100% of constraint violations are detected during validation (no invalid TimestampMaps can be saved)
- **SC-012**: CSV export-import round-trip preserves all data with zero loss (Hebrew text, timestamps, confidence scores match exactly)
- **SC-013**: Manually corrected TimestampMaps are automatically used by the pipeline with zero additional user actions required
- **SC-014**: Users can restore from backup in under 30 seconds
- **SC-015**: 90% of users successfully correct at least one timestamp on first attempt without errors
- **SC-016**: System processes CSV import of 100 verses in under 10 seconds
- **SC-017**: All validation error messages clearly identify the problem and affected verses (user comprehension rate >95% based on testing)
