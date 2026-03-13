# Research: Automated Torah Reading Audio-Visual Synchronization  
  
**Date**: 2026-01-31  
**Feature**: 001-torah-audio-text-sync  
**Purpose**: Resolve technical unknowns from Technical Context to inform implementation decisions  
  
## Research Questions  
  
### 1. Forced Alignment Library for Hebrew  
  
**Question**: Which Python library should be used for forced alignment of Hebrew audio to text?  
  
**Decision**: Use `aeneas` (Python wrapper for audio-text alignment)

> **Detailed comparison**: See [alignment-model-comparison.md](alignment-model-comparison.md) for
> in-depth evaluation of aeneas vs WhisperX, MFA, and wav2vec2.

**Rationale**:  
- Supports Unicode text (including Hebrew with diacritical marks)  
- Designed specifically for audiobook synchronization (aligns text to audio timestamps)  
- Actively maintained with Python 3.x support  
- Command-line and library interfaces available  
- Handles various audio formats (MP3, WAV, MP4)  
- Proven track record in subtitling and educational content  
  
**Alternatives Considered**:  
- **Gentle**: Forced aligner based on Kaldi ASR. Rejected because it's primarily designed for English and requires custom acoustic models for Hebrew  
- **Montreal Forced Aligner (MFA)**: Research-grade aligner. Rejected because it requires pre-trained Hebrew acoustic models and is overkill for this use case  
- **Custom Whisper + DTW**: Use OpenAI Whisper for transcription + Dynamic Time Warping. Rejected because it's more complex and aeneas provides better out-of-box alignment  
  
**Best Practices**:  
- Pre-process audio to ensure consistent format (16kHz WAV recommended for alignment)  
- Validate alignment output quality by checking timestamp gaps/overlaps  
- Allow manual correction of timestamp maps for edge cases  
  
### 2. Video Rendering Library  
  
**Question**: Which Python library should be used to generate videos with text overlay and highlighting?  
  
**Decision**: Use `moviepy` for video composition and rendering  
  
**Rationale**:  
- Pure Python library with simple API for video composition  
- Supports text overlay with customizable fonts, colors, positions  
- Can handle video clips, audio tracks, and image sequences  
- Integrates well with NumPy for frame-by-frame manipulation  
- Active community and good documentation  
- Can export to MP4 with codec control (H.264 for 360p)  
  
**Alternatives Considered**:  
- **FFmpeg (direct CLI)**: Powerful but requires complex filter chains for scrolling text. Rejected for maintainability (harder to test/debug)  
- **Manim**: Designed for mathematical animations. Rejected as overkill for simple text highlighting  
- **OpenCV + PIL**: Low-level frame manipulation. Rejected because moviepy provides higher-level abstractions  
  
**Best Practices**:  
- Use `TextClip` for Hebrew text rendering with Unicode-compatible fonts  
- Implement scrolling by calculating verse positions and using `set_position` with time-based functions  
- Render at 30fps for smooth scrolling and highlighting transitions  
- Use H.264 codec with CRF 23 for good quality-to-size ratio at 360p  
  
### 3. Hebrew Text API Client  
  
**Question**: Which library/approach should be used to retrieve Hebrew text from Sefaria?  
  
**Decision**: Use `httpx` library with Sefaria REST API v3  
  
**Rationale**:  
- based on the comparison in https://oxylabs.io/blog/httpx-vs-requests-vs-aiohttp  
  
**Alternatives Considered**:  
- **PyPi `requests` package**:  
- **PyPi `sefaria` package**: Unofficial wrapper. Rejected due to lack of maintenance and unclear API coverage  
- **Scraping Mechon Mamre**: Rejected due to legal restrictions (non-commercial only) and lack of API  
- **Local Torah database**: Rejected for initial version (would require bundling large dataset)  
  
**Best Practices**:  
- Implement retry logic with exponential backoff (API rate limits)  
- Cache responses locally to avoid repeated API calls during development  
- Validate returned text matches expected Parasha/Aliyah before alignment  
- Handle API errors gracefully (fail task with clear message per FR-002a)  
  
### 4. Hebrew Font Selection  
  
**Question**: Which font should be used to render Hebrew text with vowels and cantillation marks?  
  
**Decision**: Use "Frank Ruehl CLM" or "Taamey David CLM" fonts  
  
**Rationale**:  
- Open-source fonts with complete Hebrew Unicode coverage  
- Include vowel points (Nikkud) and cantillation marks (T'amim)  
- Designed specifically for biblical Hebrew text display  
- Available via Google Fonts or Culmus project  
- Tested for readability at small sizes (important for 360p resolution)  
  
**Alternatives Considered**:  
- **Arial/Helvetica with Hebrew support**: Lacks cantillation marks. Rejected  
- **Taamey Ashkenaz**: Similar to Taamey David. Both are acceptable choices  
- **SBL Hebrew**: Academic font. Rejected because license unclear for video redistribution  
  
**Best Practices**:  
- Bundle font files with application to ensure consistent rendering  
- Test font rendering at 360p to verify diacritical mark clarity  
- Use font size 18-24pt for verse text (adjust based on 360p testing)  
- Use bold or color change for highlighting (not just background color)  
  
### 5. Performance Goals & Resource Constraints  
  
**Question**: What are acceptable processing time and resource usage targets?  
  
**Decision**:  
- **Processing Time**: No hard limit (batch processing), but aim for <5 minutes per Aliyah on standard hardware  
- **Memory Usage**: <2GB RAM during video rendering (constrains buffer size)  
- **Disk Space**: ~500MB per Parasha output (7 Aliyot × ~70MB each at 360p)  
  
**Rationale**:  
- Spec states "No specific time constraint (batch processing acceptable)" per clarification Q5  
- 5 minutes per Aliyah allows full Torah processing in ~30 hours (acceptable for overnight batch)  
- 2GB RAM is reasonable for consumer hardware (allows running on modest VMs)  
- 360p video at H.264 CRF 23 typically yields 5-10MB per minute of video  
  
**Best Practices**:  
- Profile alignment and rendering stages separately to identify bottlenecks  
- Implement progress logging to track processing speed  
- Consider parallel processing for independent Aliyot (future optimization)  
- Monitor peak memory usage and optimize frame buffering if needed  
  
### 6. Audio Format Standardization  
  
**Question**: Should audio files be converted to a standard format before processing?  
  
**Decision**: Convert all inputs to 16kHz mono WAV before alignment  
  
**Rationale**:  
- Aeneas works best with WAV format (no codec overhead)  
- 16kHz sample rate is sufficient for speech alignment  
- Mono reduces file size and processing time (Torah readings are single-channel)  
- Preserves original files while creating normalized working copies  
  
**Best Practices**:  
- Use `pydub` or `ffmpeg-python` for audio conversion  
- Store converted files in temporary directory  
- Validate audio duration matches expected range (typical Aliyah: 5-15 minutes)  
- Keep original MP4/MP3 files for final video audio track  
  
### 7. Timestamp Map Format  
  
**Question**: What format should be used to store verse-to-timestamp mappings?  
  
**Decision**: JSON with schema validation using Pydantic models  
  
**Rationale**:  
- JSON is human-readable (supports manual correction if needed)  
- Pydantic provides automatic validation and serialization  
- Easy to version control and diff  
- Can be loaded into other tools for analysis  
  
**Schema**:  
```json  
{  
  "parasha": "Haazinu",  
  "aliyah": "Rishon",  
  "audio_file": "Haazinu_Rishon.mp4",  
  "audio_duration_sec": 612.5,  
  "verses": [  
    {  
      "reference": "Deuteronomy 32:1",  
      "hebrew_text": "הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם וַאֲדַבֵּ֑רָה        וְתִשְׁמַ֥ע הָאָ֖רֶץ אִמְרֵי־פִֽי׃",  
      "start_sec": 0.0,  
      "end_sec": 4.2  
    }  
  ]  
}  
```  
  
**Best Practices**:  
- Include metadata (Parasha, Aliyah) for traceability  
- Store Hebrew text in map for debugging/validation  
- Use ISO references (book/chapter/verse) for Sefaria queries  
- Validate that timestamps are monotonically increasing  
  
**Execution**: All Python commands should be run with `uv run` prefix per UV best practices (e.g., `uv run pytest`, `uv run torah-sync`)  
  
  
## Technology Stack Summary  
  
| Component | Technology | Version/Notes |
|-----------|-----------|---------------|
| **Language** | Python | 3.13 |
| **Forced Alignment** | aeneas | Latest stable |
| **Video Rendering** | moviepy | Latest stable |
| **HTTP Client** | httpx | For Sefaria API |
| **Audio Processing** | pydub | For format conversion |
| **Font** | Frank Ruehl CLM / Taamey David CLM | Bundled |
| **Data Models** | Pydantic | For JSON validation |
| **Testing** | pytest | Per constitution |
| **Package Management** | UV | Per constitution |
| **Configuration** | dynaconf | Multi-layered config management |
| **Logging** | loguru | Structured logging with automatic JSON serialization |  
  
## Next Steps  
  
1. **Phase 1: Data Model** - Define Pydantic models for Parasha, Aliyah, Pasuk, TimestampMap  
2. **Phase 1: Contracts** - Define CLI interface and expected inputs/outputs  
3. **Phase 1: Quickstart** - Document setup steps (font installation, UV dependencies)  
4. **Phase 2: Tasks** - Break down implementation into testable user stories  
  
## Open Questions  
  
None remaining - all NEEDS CLARIFICATION items resolved.  
  
### 8. Configuration Management  
  
**Question**: How should the application manage configuration for different environments and user preferences?  
  
**Decision**: Use `dynaconf` for configuration management  
  
**Rationale**:  
- Multi-layered configuration: defaults, environment variables, config files, CLI args  
- Support for multiple file formats (TOML, YAML, JSON, INI)  
- Environment-specific settings (development, testing, production)  
- Validation and type casting built-in  
- Secret management support  
- Well-maintained and widely adopted in Python ecosystem  
  
**Configuration Structure**:  
```toml  
# settings.toml (default configuration)  
[default]  
cache_dir = "data/cache"  
output_dir = "output/videos"  
log_level = "INFO"  
font_path = "fonts/FrankRuhl-Regular.ttf"  
parallel_workers = 1  
  
[default.video]  
resolution = [640, 360]  
fps = 30  
codec = "h264"  
crf = 23  
  
[default.sefaria]  
base_url = "https://www.sefaria.org/api"  
retry_attempts = 3  
retry_backoff_base = 2  
cache_responses = true  
  
[default.alignment]  
audio_sample_rate = 16000  
convert_to_mono = true  
min_confidence = 0.90  
  
# Environment-specific overrides  
[development]  
log_level = "DEBUG"  
cache_dir = ".cache"  
  
[production]  
log_level = "WARNING"  
parallel_workers = 4  
```  
  
**Best Practices**:  
- Store defaults in `settings.toml`  
- Override with environment variables: `TORAH_SYNC_CACHE_DIR`  
- CLI arguments take highest precedence  
- Keep secrets in separate `.secrets.toml` (gitignored)  
- Validate configuration on startup  
  
**Alternatives Considered**:  
- **python-decouple**: Simpler but lacks hierarchical config. Rejected for insufficient features  
- **configparser**: Standard library but only INI format. Rejected for limited format support  
- **pydantic-settings**: Good for validation but requires more boilerplate. Rejected for complexity  
- **Manual env vars + argparse**: No file support, hard to maintain. Rejected  
  
**Dependencies Added**: `dynaconf`  
