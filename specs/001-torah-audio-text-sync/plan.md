# Implementation Plan: Automated Torah Reading Audio-Visual Synchronization  
  
**Branch**: `001-torah-audio-text-sync` | **Date**: 2026-01-31 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-torah-audio-text-sync/spec.md`  
  
**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.  
  
## Summary  
  
Create a system that generates Torah reading videos with Hebrew text displayed alongside audio. Phase 1 produces static text videos (all verses visible); Phase 2 adds dynamic verse highlighting (depends on fine-tuned alignment from spec 002). The system processes audio files organized by Parasha and Aliyah, retrieves corresponding Hebrew text with vowels and cantillation marks, performs forced alignment at the verse level, and renders 360p MP4 videos with text overlay and metadata display.
  
## Technical Context  
  
**Language/Version**: Python 3.13
**Primary Dependencies**: aeneas (forced alignment), moviepy (video rendering), httpx (Sefaria API client), pydub (audio conversion), dynaconf (configuration), loguru (logging)
**Storage**: File-based (audio inputs, timestamp maps as JSON, video outputs)  
**Testing**: pytest  
**Target Platform**: Linux/macOS development environment, batch processing workstation  
**Project Type**: Single project (CLI-based batch processing pipeline)  
**Performance Goals**: <5 minutes per Aliyah processing time (target), <2GB RAM during rendering  
**Constraints**: Video output at 360p (640x360) resolution, verse synchronization within 0.5 seconds, 95% verse boundary accuracy  
**Scale/Scope**: Process entire Hebrew Bible (Torah + Haftarot), approximately 300+ audio files, ~500MB per Parasha output  
  
## Constitution Check  
  
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*  
  
**I. Code Quality First**: ✅ PASS  
- File size limit (≤2048 tokens) applies  
- Type hints required (mypy strict)  
- Cyclomatic complexity ≤10 per function  
- No linting errors  
  
**II. Test-Driven Development**: ✅ PASS  
- pytest framework will be used  
- TDD methodology required  
- Coverage ≥90% for new code  
- Tests organized in contract/, integration/, unit/  
  
**III. User Experience Consistency**: ✅ PASS  
- CLI interface for batch processing  
- Consistent error messages required  
- Structured logging (JSON format)  
  
**IV. Performance by Design**: ✅ PASS  
- Performance targets defined: <5 min per Aliyah, <2GB RAM  
- Success criteria: 0.5s sync accuracy, 95% boundary accuracy  
  
**V. Library-First Architecture**: ✅ PASS  
- Design as modular libraries:  
  - Audio parsing library  
  - Text retrieval library  
  - Forced alignment library  
  - Video rendering library  
  - CLI orchestration layer  
  
**VI. Dependency Management & Tooling Standards**: ✅ PASS  
- UV will be used exclusively for package management  
- pyproject.toml for dependencies  
  
**VII. Observability & Debugging**: ✅ PASS  
- Text I/O pattern: stdin/args → stdout, errors → stderr  
- Structured logging for processing pipeline  
- Error context with file paths and stack traces  
  
**Python Standards**: ✅ PASS  
- No `__init__.py` files (implicit namespace packages)  
- Type hints for all function signatures  
- f-strings for formatting (f'{variable=}' pattern)  
  
**Red Hat Standards**: ✅ PASS  
- Specification-driven development followed  
- Clear separation between spec and implementation  
- Success criteria established before implementation  
  
**Overall**: ✅ ALL GATES PASSED - Proceed to implementation  
  
## Project Structure  
  
### Documentation (this feature)  
  
```text  
specs/001-torah-audio-text-sync/  
├── spec.md              # Feature specification  
├── plan.md              # This file (/speckit.plan command output)  
├── research.md          # Phase 0 output (/speckit.plan command)  
├── data-model.md        # Phase 1 output (/speckit.plan command)  
├── quickstart.md        # Phase 1 output (/speckit.plan command)  
├── contracts/           # Phase 1 output (/speckit.plan command)  
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)  
```  
  
### Source Code (repository root)  
  
```text  
src/  
├── models/              # Data models (Parasha, Aliyah, Pasuk, TimestampMap, etc.)  
├── services/            # Core processing services
│   ├── audio/          # Audio file parsing and validation (pydub)
│   ├── text/           # Hebrew text retrieval (httpx + Sefaria API)
│   │   ├── sefaria_client.py      # Low-level Sefaria API wrapper
│   │   ├── cache.py                # Caching layer for API responses
│   │   ├── parasha_fetcher.py     # Batch text fetcher (NEW)
│   │   └── hebrew_renderer.py     # Text rendering utilities
│   ├── alignment/      # Forced alignment engine (aeneas)
│   └── video/          # Video rendering with text overlay (moviepy)  
├── cli/                # CLI entry points for batch processing
└── lib/                # Shared utilities (logging, file I/O, validation)

data/
├── aliyah_ranges.toml  # Aliyah verse range configuration (NEW)
├── audio/              # Input audio files
└── cache/              # Cached API responses and timestamp maps

tests/  
├── contract/           # API contract tests (Sefaria API, CLI interface)  
├── integration/        # Integration tests (end-to-end pipeline)  
└── unit/               # Unit tests for individual modules  
```  
  
**Structure Decision**: Single project structure selected. This is a batch processing pipeline with CLI interface, not a web or mobile application. All components are tightly integrated around the video generation workflow, so a monolithic structure with modular internal organization is appropriate. The library-first principle is satisfied through clear module boundaries within src/services/.

## Text Fetching Architecture Details

### Module Breakdown: `src/services/text/`

**Purpose**: Retrieve Hebrew text with vowels and cantillation marks from Sefaria API, optimized for batch processing.

**Components**:

1. **`sefaria_client.py`** (Existing)
   - Low-level HTTP client for Sefaria API v3
   - Implements `get_verse()` and `get_range()` per API contract
   - Handles retries, rate limiting, error responses
   - Protocol: `HebrewTextSource`

2. **`cache.py`** (Existing)
   - File-based caching of Sefaria responses
   - Cache location: `data/cache/sefaria/{book}_{chapter}_{verse}.json`
   - Wraps `SefariaClient` as `CachedSefariaClient`

3. **`parasha_fetcher.py`** (NEW - Phase 2 Enhancement)
   - Aliyah-aware batch text fetcher
   - Loads verse ranges from `data/aliyah_ranges.toml`
   - Maps (Parasha name, Aliyah name) → (book, chapter range, verse range)
   - Calls `SefariaClient.get_range()` for entire Aliyah
   - Returns structured list of (reference, hebrew_text) tuples
   - Reduces API calls by 86-97% vs. per-verse retrieval

4. **`hebrew_renderer.py`** (Existing)
   - Hebrew text rendering utilities
   - BiDi text handling, font rendering
   - Not related to fetching (separate concern)

**Dependencies**:
```text
ProcessingPipeline
    │
    ├─> ParashaTextFetcher (composition)
    │       │
    │       ├─> AliyahRange config (loads from TOML)
    │       └─> CachedSefariaClient (composition)
    │               │
    │               └─> SefariaClient (composition)
    │
    └─> (fallback) CachedSefariaClient (direct usage for testing)
```

**Configuration File**: `data/aliyah_ranges.toml`

**Format**:
```toml
# Format: [parasha_name_normalized.aliyah_name_normalized]
# Normalization: Hebrew names in lowercase, spaces removed

[haazinu.rishon]
book = "Deuteronomy"
chapter_start = 32
verse_start = 1
chapter_end = 32
verse_end = 6

[haazinu.sheni]
book = "Deuteronomy"
chapter_start = 32
verse_start = 7
chapter_end = 32
verse_end = 12

# Total entries: ~300 (54 Parashot × ~7 Aliyot each)
```

**Implementation Priority**:
- **MVP (Phase 1)**: Use `CachedSefariaClient` directly (per-verse or manual range)
- **Phase 2 Enhancement**: Add `ParashaTextFetcher` for production optimization
- **Phase 3**: Populate `aliyah_ranges.toml` for all 54 Torah Parashot

**Performance Targets**:
- Single Aliyah text fetch: <1 second (batch) vs. 5-10 seconds (per-verse)
- API call reduction: 80-97% (target PR-003 from spec)
- Cache hit rate: >95% for re-processing same Parashot

## Complexity Tracking  
  
> **Fill ONLY if Constitution Check has violations that must be justified**  
  
No violations. All constitution requirements met with the proposed architecture.  
