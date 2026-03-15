# Feature Specification: Automated Torah Reading Audio-Visual Synchronization

<!-- Edited by Claude Opus 4.6 -->

**Feature Branch**: `001-torah-audio-text-sync`
**Created**: 2026-01-31
**Updated**: 2026-03-15
**Status**: Draft
**Input**: User description: "Automated Torah Reading Audio-Visual Synchronization - Create synchronized videos of Torah readings where Hebrew text highlights in real-time following the audio"  
  
## Clarifications  
  
### Session 2026-01-31  
  
- Q: How should the system identify which Parasha and Aliyah an audio file contains? → A: Audio files follow a standardized naming convention using Hebrew (e.g., "פרשת האזינו - ראשון - נוסח אשכנז.mp4")  
- Q: When the Hebrew text source (Sefaria API) is unavailable or returns incomplete data, what should the system do? → A: Fail the processing task with clear error message for retry later  
- Q: What video format and resolution should the system generate? → A: 360p (revised from 144p)  
- Q: How should the Hebrew text be displayed and what happens when there are more verses than fit on screen? → A: Display multiple verses with auto-scroll to keep highlighted verse centered  
- Q: What is an acceptable processing time to generate one synchronized video for a single Aliyah? → A: No specific time constraint (batch processing acceptable)  
  
## User Scenarios & Testing *(mandatory)*  
  
### User Story 1 - View Torah Reading Video with Text (Priority: P1)

A student of Torah reading wants to follow along with a visual guide. They need to see the Hebrew text (with vowels and cantillation marks) displayed alongside the audio, creating a reference experience where all verses are visible while the reader recites.

**Why this priority**: This is the foundational deliverable - generating a video with Hebrew text and audio. Without this, no further enhancements (highlighting, metadata) are possible.

**Independent Test**: Can be fully tested by playing a video for a single Aliyah (portion) and verifying that Hebrew text is displayed clearly with proper diacritical marks while audio plays.

**Phase note**: Verse highlighting (dynamic color changes synchronized to audio) is deferred to Phase 2, which depends on fine-tuned alignment via spec 002 (Manual Alignment Correction). This phase produces static text display only.

**Acceptance Scenarios**:

1. **Given** an audio file for one Aliyah, **When** the system processes it, **Then** an MP4 video is generated with all verses displayed as static Hebrew text with audio
2. **Given** Hebrew text with vowels and cantillation marks (T'amim), **When** the video displays text, **Then** all diacritical marks are clearly visible and correctly positioned
3. **Given** a generated video, **When** the user plays it, **Then** the audio is synchronized with the video duration and all verses are readable
4. **Given** more verses than fit on screen, **When** the video is generated, **Then** text layout accommodates all verses with proper spacing  
  
---  
  
### User Story 2 - Identify Context Within Torah Portion (Priority: P2)  
  
A user watching a Torah reading video wants to know which Parasha (weekly portion), which Aliyah (section), and which verse they are currently viewing without having prior knowledge of the structure.  
  
**Why this priority**: Context helps users navigate the Torah and understand their location within the broader text structure. This enhances learning but isn't required for the basic follow-along experience.  
  
**Independent Test**: Can be tested independently by checking that metadata (Parasha name, Aliyah number, verse reference) is consistently visible throughout any video playback.  
  
**Acceptance Scenarios**:  
  
1. **Given** a video is playing, **When** the user looks at the screen, **Then** the Parasha name (e.g., "Haazinu") is displayed  
2. **Given** a video is playing, **When** the user looks at the screen, **Then** the current Aliyah name (e.g., "Rishon", "Sheni") is displayed  
3. **Given** a video is playing, **When** the user looks at the screen, **Then** the current verse reference is displayed  
4. **Given** metadata is displayed, **When** the highlighted verse changes, **Then** the verse reference updates to reflect the new position  
  
---  
  
### User Story 3 - Process Multiple Torah Portions (Priority: P3)  
  
A content creator wants to generate synchronized videos for all Torah portions (Parashot) across the entire Hebrew Bible, with each portion broken down into its traditional Aliyot (typically seven sections).  
  
**Why this priority**: Scaling to the full Torah enables comprehensive educational content, but the feature can provide value with even a single portion. This is an expansion goal.  
  
**Independent Test**: Can be tested by processing multiple Parasha files and verifying each produces correctly synchronized output with proper segmentation into Aliyot.  
  
**Acceptance Scenarios**:  
  
1. **Given** audio files for multiple Parashot, **When** the system processes them, **Then** each Parasha generates a separate set of videos (one per Aliyah)  
2. **Given** a Parasha with seven Aliyot+ maftir + Haftara , **When** processing completes, **Then** seven + maftir + Haftara synchronized videos are produced  
3. **Given** audio from different Torah portions, **When** the system retrieves corresponding text, **Then** the correct verses for each portion are matched to the audio  
  
  
---  
  
### Edge Cases  
  
- When the Hebrew text source is unavailable or returns incomplete data, the system fails the processing task with a clear error message and logs the failure for manual or automated retry  
- How does the system handle audio files that don't cleanly align to verse boundaries (reader takes long pauses, commentary, or non-text vocalizations)?  
- What happens when cantillation marks (T'amim) don't perfectly match the audio performance (different musical traditions)?  
- What happens if the video rendering process fails midway through a ALiya?  
  
## Requirements *(mandatory)*  
  
### Functional Requirements  
  
- **FR-001**: System MUST accept audio input files in common formats (MP4, MP3, WAV) following a standardized naming convention that identifies the Parasha and Aliyah (e.g., "פרשת האזינו - ראשון - נוסח אשכנז.mp4", "פרשת בראשית - שני - נוסח אשכנז.mp3")  
- **FR-002**: System MUST retrieve Hebrew text with vowels (Nikkud) and cantillation marks (T'amim) for any specified Torah portion using batch retrieval strategies to minimize API requests  
- **FR-002a**: System MUST fail processing with a clear error message when Hebrew text source is unavailable or returns incomplete data, logging the failure for retry  
- **FR-003**: System MUST synchronize Hebrew text to audio at the verse (Pasuk) level, identifying start and end timestamps for each verse  
- **FR-004**: System MUST generate video output in MP4 format at 360p (640x360) resolution with Hebrew text displayed alongside audio
- **FR-004a** *(Phase 2)*: System MUST visually highlight the current verse as it is being read (depends on fine-tuned alignment from spec 002)
- **FR-005**: System MUST display Hebrew text in a clear, high-contrast font that preserves diacritical marks
- **FR-005a**: System MUST display multiple verses on screen simultaneously with proper spacing and layout
- **FR-005b** *(Phase 2)*: System MUST implement automatic scrolling to keep the currently highlighted verse centered in the visible area
- **FR-006** *(Phase 2)*: System MUST differentiate the currently active verse from upcoming or past verses through visual styling (highlighting, opacity changes, or color)  
- **FR-007**: System MUST overlay metadata showing the Parasha name, Aliyah name, and current verse reference  
- **FR-008**: System MUST process audio files that correspond to individual Aliyot (one Aliyah per audio file)  
- **FR-010**: System MUST use legally permissible Hebrew text sources (open-source or appropriately licensed)  
- **FR-011**: System MUST preserve attribution to the original audio source (Yoseph Joseph Bodenhaimer recordings)  
- **FR-012**: System MUST handle Torah portions from the complete Hebrew Bible (all Parashot)

### Performance Requirements

- **PR-001**: System SHOULD minimize API requests to Hebrew text sources through batch retrieval strategies
- **PR-002**: System SHOULD fetch entire Aliyah verse ranges in a single API request rather than per-verse requests
- **PR-003**: System SHOULD reduce API calls by at least 80% compared to naive per-verse retrieval

### Key Entities

*Implementation names in parentheses. See `tmp/db_erd.md` (ERD v2) for full schema.*

- **Playlist** (replaces Parasha): A weekly Torah portion (e.g., "Haazinu"). Contains multiple Aliyot. Identified by name and book/chapter/verse range. Maps to a YouTube playlist.
- **Alya** (replaces Aliyah): A subdivision of a Parasha, `order_num` 1-7 for Torah aliyot, 8 for maftir, 9 for haftara. Contains multiple verses. Associated with one audio file.
- **AlyaRange** (replaces AliyahRange): Verse range(s) for an alya. Supports compound Haftarot with multiple non-consecutive ranges. Stored in DuckDB `alya_ranges` table.
- **PasukAlignment** (replaces VerseTimestamp): Per-verse alignment row — reference, hebrew_text, start_time, end_time, confidence. Tracks `original_start_time`/`original_end_time` for corrections.
- **AlignmentRun** (replaces TimestampMap): Result of a forced alignment run. Links to `alya_audio`. Produces many `PasukAlignment` rows.
- **AlyaAudio** (replaces AudioSource): Audio file metadata (MP4/MP3/WAV). One-to-one with Alya. Sourced from Yoseph Joseph Bodenhaimer's recordings.
- **AlyaVideo** (replaces SynchronizedVideo): Output video in MP4 at 360p (640x360). One-to-one with Alya.
- **Hebrew Text Source**: Protocol interface for vowelized Hebrew text with cantillation marks (Sefaria API).

  
## Success Criteria *(mandatory)*  
  
### Measurable Outcomes  
  
- **SC-001**: A viewer can see all Hebrew text clearly displayed while audio plays, enabling them to follow along with the reading
- **SC-001a** *(Phase 2)*: A viewer can identify which verse is being read at any moment via dynamic highlighting
- **SC-002**: Hebrew text rendering at 360p resolution preserves all vowel points (Nikkud) and cantillation marks (T'amim) with sufficient clarity for reading practice
- **SC-003** *(Phase 2)*: Verse highlighting transitions occur within 0.5 seconds of the actual verse boundary in the audio (perceived as real-time synchronization, depends on fine-tuned alignment from spec 002)  
- **SC-004**: Metadata (Parasha, Aliyah, verse reference) is visible and readable throughout the entire video playback  
- **SC-005**: The system successfully processes and generates synchronized videos for at least one complete Parasha (with 7 Aliyot) as proof of scalability  
- **SC-006**: Generated videos comply with copyright requirements (open-source text, proper attribution for audio)  
- **SC-007**: Users can identify which Aliyah they are watching within 5 seconds of starting video playback  
- **SC-008** *(Phase 2)*: 95% of verse boundaries align accurately with the audio (allowing for minor timing variations due to reading style, requires manual alignment correction from spec 002)  
  
## Assumptions  
  
- Audio files are already segmented by Aliyah (one audio file per Aliyah, not combined)  
- Audio quality is sufficient for automated speech-to-text alignment (minimal background noise, clear pronunciation)  
- Video generation is a batch processing operation with no specific time constraints (processing can take as long as needed per Aliyah)  
- Hebrew text sources (Sefaria or equivalent) provide accurate vowelization and cantillation marks matching traditional Ashkenazi reading style  
- Standard industry tools for forced alignment can handle Hebrew text with diacritical marks  
- Target audience has basic familiarity with Torah structure (understands concepts of Parasha, Aliyah, verse)  
- Videos will be used for educational/religious purposes (non-commercial or appropriately licensed)  
- Initial implementation focuses on Ashkenazi pronunciation and cantillation tradition  
- Output videos will be distributed in a manner consistent with the audio source's licensing (Yoseph Joseph Bodenhaimer's permissions)  
  
## Dependencies  
  
- Access to Yoseph Joseph Bodenhaimer's Torah reading recordings (via YouTube download or direct source)  
- Access to open-source Hebrew text database with vowels and cantillation marks (e.g., Sefaria API)  
- Audio-to-text forced alignment capability for Hebrew language
- Aliyah verse range configuration (mapping Parasha/Aliyah to biblical references)
- Video rendering capability for text overlay and highlighting effects  
  
## Scope  
  
### In Scope  
  
- Synchronizing audio with Hebrew text at the verse level  
- Generating videos with real-time verse highlighting  
- Displaying metadata (Parasha, Aliyah, verse, Haftara reference)  
- Processing entire Parashot broken into individual Aliyot  
- Supporting audio formats: MP4, MP3, WAV  
- Using legally permissible text sources  
- Handling sample data (Parashat Haazinu - Rishon and Sheni Aliyot)  
  
### Out of Scope  
  
- Interactive video controls beyond standard play/pause (e.g., clicking on verse to jump to that timestamp)  
- Multiple language translations or transliterations  
- Support for Sephardic or other non-Ashkenazi cantillation traditions in initial version  
- Real-time streaming (focus is on pre-generated video files)  
- User-uploaded audio files (focus is on specific source: Yoseph Joseph Bodenhaimer)  
- Automated downloading from YouTube (manual audio extraction is acceptable)  
- Mobile app development (videos can be played in standard video players)  
- Commentary or explanatory text beyond verse highlighting  
- Audio synchronization at sub-verse granularity (word-level or syllable-level highlighting)  
