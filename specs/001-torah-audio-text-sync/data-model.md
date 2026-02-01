# Data Model: Automated Torah Reading Audio-Visual Synchronization  
  
**Date**: 2026-01-31  
**Feature**: 001-torah-audio-text-sync  
**Purpose**: Define core entities and their relationships for Torah audio-text synchronization  
  
## Entity Definitions  
  
### Parasha  
  
Represents a weekly Torah portion from the Hebrew Bible.  
  
**Fields**:  
- `name: str` - Name of the Parasha (e.g., "Haazinu", "Bereshit")  
- `book: str` - Torah book name (e.g., "Deuteronomy", "Genesis")  
- `chapter_start: int` - Starting chapter number  
- `verse_start: int` - Starting verse number  
- `chapter_end: int` - Ending chapter number  
- `verse_end: int` - Ending verse number  
- `aliyot: list[Aliyah]` - List of Aliyot for this Parasha (typically 7)  
  
**Validation Rules**:  
- `name` must be non-empty  
- `chapter_start` ≤ `chapter_end`  
- If `chapter_start == chapter_end`, then `verse_start` < `verse_end`  
- `aliyot` length typically 7 (can vary for special Parashot)  
  
**Relationships**:  
- **Contains many** Aliyot (1:N)  
  
### Aliyah  
  
Represents a subdivision of a Parasha, traditionally one of seven sections.  
  
**Fields**:  
- `name: str` - Aliyah name (e.g., "Rishon", "Sheni", "Shlishi", "Revi'i", "Chamishi", "Shishi", "Shevi'i", "Maftir")  
- `parasha_name: str` - Parent Parasha name (foreign key)  
- `order: int` - Sequence number within Parasha (1-7 typically, 8 for Maftir)  
- `verses: list[Pasuk]` - List of verses in this Aliyah  
- `audio_file_path: Path` - Path to audio recording file  
- `duration_seconds: float` - Total audio duration  
  
**Validation Rules**:  
- `name` must be one of canonical Aliyah names  
- `order` must be 1-8  
- `audio_file_path` must exist and follow naming convention `{parasha_name}_{aliyah_name}.{ext}`  
- `duration_seconds` > 0  
  
**Relationships**:  
- **Belongs to one** Parasha (N:1)  
- **Contains many** Pasuk (verses) (1:N)  
- **Has one** TimestampMap (1:1)  
  
**State Transitions**:  
- `pending` → Audio file identified, not yet processed  
- `aligning` → Forced alignment in progress  
- `aligned` → Timestamps generated successfully  
- `rendering` → Video generation in progress  
- `completed` → Video output ready  
- `failed` → Processing error occurred  
  
### Pasuk (Verse)  
  
Represents a single verse of Hebrew text with vowels and cantillation marks.  
  
**Fields**:  
- `reference: str` - Canonical verse reference (e.g., "Deuteronomy 32:1")  
- `book: str` - Book name (e.g., "Deuteronomy")  
- `chapter: int` - Chapter number  
- `verse: int` - Verse number within chapter  
- `hebrew_text: str` - Hebrew text with Nikkud (vowels) and T'amim (cantillation marks)  
- `start_timestamp: float` - Start time in audio (seconds)  
- `end_timestamp: float` - End time in audio (seconds)  
- `aliyah_name: str` - Parent Aliyah name (foreign key)  
  
**Validation Rules**:  
- `reference` format: `{Book} {chapter}:{verse}`  
- `chapter` > 0, `verse` > 0  
- `hebrew_text` must contain Hebrew Unicode characters (U+0590 to U+05FF range)  
- `start_timestamp` ≥ 0  
- `end_timestamp` > `start_timestamp`  
- `end_timestamp` - `start_timestamp` should be reasonable (e.g., 1-30 seconds per verse)  
  
**Relationships**:  
- **Belongs to one** Aliyah (N:1)  
  
### Haftara  
  
Represents a weekly Prophets (Neviim) portion read after the Torah portion.  
  
**Fields**:  
- `name: str` - Haftara name (typically matches associated Parasha)  
- `book: str` - Prophets book name (e.g., "Isaiah", "Jeremiah")  
- `chapter_start: int` - Starting chapter number  
- `verse_start: int` - Starting verse number  
- `chapter_end: int` - Ending chapter number  
- `verse_end: int` - Ending verse number  
- `parasha_name: str` - Associated Parasha name (foreign key)  
  
**Validation Rules**:  
- Same chapter/verse validation as Parasha  
- `book` must be from Neviim (Prophets) section  
  
**Relationships**:  
- **Associated with one** Parasha (1:1 or 0:1 - some Parashot have multiple Haftarot)  
  
**Note**: Haftara processing follows the same pipeline as Aliyot but is tracked separately.  
  
### Audio Source  
  
Represents an audio recording file for one Aliyah.  
  
**Fields**:  
- `file_path: Path` - Absolute path to audio file  
- `format: str` - File extension (e.g., "mp4", "mp3", "wav")  
- `duration_seconds: float` - Total audio duration  
- `sample_rate: int` - Audio sample rate in Hz (e.g., 44100, 48000)  
- `channels: int` - Number of audio channels (1 for mono, 2 for stereo)  
- `attribution: str` - Source attribution (e.g., "Yoseph Joseph Bodenhaimer")  
- `parasha_name: str` - Extracted from filename  
- `aliyah_name: str` - Extracted from filename  
  
**Validation Rules**:  
- `file_path` must exist on filesystem  
- `format` must be one of: ["mp4", "mp3", "wav"]  
- Filename must match pattern: `{parasha_name}_{aliyah_name}.{format}`  
- `duration_seconds` > 0  
- `sample_rate` typically 16000-48000 Hz  
- `channels` should be 1 (mono preferred for alignment)  
  
**Relationships**:  
- **Belongs to one** Aliyah (1:1)  
  
### Hebrew Text Source  
  
Represents the source of Hebrew text (Sefaria API).  
  
**Fields**:  
- `base_url: str` - API base URL (e.g., "https://www.sefaria.org/api")  
- `text_version: str` - Specific text version to use (e.g., "Tanach with Ta'amei Hamikra")  
- `language: str` - Language code (e.g., "he" for Hebrew)  
- `include_vowels: bool` - Whether to include Nikkud (vowel points)  
- `include_cantillation: bool` - Whether to include T'amim (cantillation marks)  
  
**Validation Rules**:  
- `base_url` must be valid URL  
- `include_vowels` and `include_cantillation` must both be `true` for this feature  
  
**Relationships**:  
- **Provides text for many** Pasuk (1:N via API calls)  
  
### Synchronized Video  
  
Represents the output video file with highlighted text overlay.  
  
**Fields**:  
- `file_path: Path` - Output video file path  
- `format: str` - Video container format ("mp4")  
- `resolution: tuple[int, int]` - Video resolution (640, 360) for 360p  
- `frame_rate: int` - Frames per second (30 fps)  
- `codec: str` - Video codec ("h264")  
- `duration_seconds: float` - Total video duration (matches audio)  
- `parasha_name: str` - Associated Parasha  
- `aliyah_name: str` - Associated Aliyah  
- `created_at: datetime` - Timestamp of video generation  
  
**Validation Rules**:  
- `resolution` must be (640, 360)  
- `format` must be "mp4"  
- `frame_rate` should be 30  
- `duration_seconds` must match source audio duration  
- Output filename pattern: `{parasha_name}_{aliyah_name}_sync.mp4`  
  
**Relationships**:  
- **Generated from one** Aliyah (1:1)  
- **Uses one** TimestampMap (1:1)  
  
### Timestamp Map  
  
Represents the mapping of each verse to its precise audio timestamps.  
  
**Fields**:  
- `parasha_name: str` - Parasha name  
- `aliyah_name: str` - Aliyah name  
- `audio_file_path: Path` - Source audio file  
- `audio_duration_seconds: float` - Total audio duration  
- `verse_timestamps: list[VerseTimestamp]` - List of verse-to-timestamp mappings  
- `alignment_quality: float` - Alignment confidence score (0.0-1.0)  
- `generated_at: datetime` - When alignment was performed  
- `manual_corrections: int` - Count of manually adjusted timestamps  
  
**Validation Rules**:  
- `verse_timestamps` must be sorted by `start_timestamp` (monotonically increasing)  
- No timestamp gaps > 5 seconds (indicates missing verse)  
- No timestamp overlaps (end of verse N < start of verse N+1)  
- `alignment_quality` should be > 0.85 for acceptable results  
- First verse `start_timestamp` should be near 0.0  
- Last verse `end_timestamp` should be near `audio_duration_seconds`  
  
**Relationships**:  
- **Belongs to one** Aliyah (1:1)  
- **Contains many** VerseTimestamp (1:N)  
  
**Storage Format**: JSON file at `outputs/{parasha_name}_{aliyah_name}_timestamps.json`  
  
### VerseTimestamp  
  
Embedded object within TimestampMap (not a top-level entity).  
  
**Fields**:  
- `reference: str` - Verse reference (e.g., "Deuteronomy 32:1")  
- `hebrew_text: str` - Hebrew text (for debugging/validation)  
- `start_sec: float` - Start time in audio (seconds)  
- `end_sec: float` - End time in audio (seconds)  
  
**Validation Rules**:  
- `start_sec` ≥ 0  
- `end_sec` > `start_sec`  
- `end_sec - start_sec` typically 1-30 seconds  
  
## Entity Relationship Diagram  
  
```text  
Parasha (1) ──────< (N) Aliyah (1) ──────< (N) Pasuk  
    │                      │  
    │                      │  
    │                      ├──────< (1) Audio Source  
    │                      │  
    │                      ├──────< (1) Timestamp Map (1) ──────< (N) VerseTimestamp  
    │                      │  
    │                      └──────< (1) Synchronized Video  
    │  
    └──────< (1) Haftara  
  
  
Hebrew Text Source (1) ──────< (N) Pasuk [via API calls]  
```  
  
## Implementation Notes  
  
### Pydantic Model Examples  
  
```python  
from pydantic import BaseModel, Field, validator  
from pathlib import Path  
from datetime import datetime  
  
class Pasuk(BaseModel):  
    reference: str  
    book: str  
    chapter: int = Field(gt=0)  
    verse: int = Field(gt=0)  
    hebrew_text: str  
    start_timestamp: float = Field(ge=0.0)  
    end_timestamp: float  
    aliyah_name: str  
  
    @validator('end_timestamp')  
    def validate_end_after_start(cls, v, values):  
        if 'start_timestamp' in values and v <= values['start_timestamp']:  
            raise ValueError('end_timestamp must be > start_timestamp')  
        return v  
  
class VerseTimestamp(BaseModel):  
    reference: str  
    hebrew_text: str  
    start_sec: float = Field(ge=0.0)  
    end_sec: float  
  
    @validator('end_sec')  
    def validate_duration(cls, v, values):  
        if 'start_sec' in values and v <= values['start_sec']:  
            raise ValueError('end_sec must be > start_sec')  
        return v  
  
class TimestampMap(BaseModel):  
    parasha_name: str  
    aliyah_name: str  
    audio_file_path: Path  
    audio_duration_seconds: float = Field(gt=0.0)  
    verse_timestamps: list[VerseTimestamp]  
    alignment_quality: float = Field(ge=0.0, le=1.0)  
    generated_at: datetime  
    manual_corrections: int = Field(ge=0, default=0)  
```  
  
### Key Design Decisions  
  
1. **Immutable Entities**: Parasha, Aliyah metadata are read-only after initialization  
2. **Validation on Construction**: Use Pydantic validators to enforce constraints early  
3. **File Path Handling**: Use `pathlib.Path` for cross-platform compatibility  
4. **JSON Serialization**: Pydantic provides automatic `model_dump_json()` for storage  
5. **State Machine**: Aliyah state transitions tracked for pipeline monitoring  
  
## Next Steps  
  
Phase 1 continues with:  
- CLI contract definition (`contracts/`)  
- Quickstart guide (`quickstart.md`)  
