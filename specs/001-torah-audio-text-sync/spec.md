# Feature Specification: Automated Torah Reading Audio-Visual Synchronization

**Feature Branch**: `001-torah-audio-text-sync`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "Automated Torah Reading Audio-Visual Synchronization - Create synchronized videos of Torah readings where Hebrew text highlights in real-time following the audio"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Synchronized Torah Reading Video (Priority: P1)

A student of Torah reading wants to practice their chanting by following along with a visual guide. They need to see the Hebrew text (with vowels and cantillation marks) highlight in real-time as the reader recites each verse, creating a "follow the reader" experience.

**Why this priority**: This is the core value proposition - enabling users to visually follow along with professional Torah readings. Without this, the feature has no purpose.

**Independent Test**: Can be fully tested by playing a video for a single Aliyah (portion) and verifying that each verse highlights synchronously with the audio, delivering immediate educational value.

**Acceptance Scenarios**:

1. **Given** a video file containing a Torah reading for one Aliyah, **When** the reader begins reciting a verse, **Then** that verse is visually highlighted in the display
2. **Given** the reader is currently on verse 5, **When** the reader finishes verse 5 and begins verse 6, **Then** the highlight moves from verse 5 to verse 6 with smooth transition
3. **Given** a video is playing, **When** the user pauses the video, **Then** the current verse remains highlighted at the point of pause
4. **Given** Hebrew text with vowels and cantillation marks (T'amim), **When** the video displays text, **Then** all diacritical marks are clearly visible and correctly positioned

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

- What happens when the Hebrew text source is unavailable or returns incomplete data?
- How does the system handle audio files that don't cleanly align to verse boundaries (reader takes long pauses, commentary, or non-text vocalizations)?
- What happens when cantillation marks (T'amim) don't perfectly match the audio performance (different musical traditions)?
- What happens if the video rendering process fails midway through a ALiya?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept audio input files in common formats (MP4, MP3, WAV)
- **FR-002**: System MUST retrieve Hebrew text with vowels (Nikkud) and cantillation marks (T'amim) for any specified Torah portion
- **FR-003**: System MUST synchronize Hebrew text to audio at the verse (Pasuk) level, identifying start and end timestamps for each verse
- **FR-004**: System MUST generate video output where the current verse is visually highlighted as it is being read
- **FR-005**: System MUST display Hebrew text in a clear, high-contrast font that preserves diacritical marks
- **FR-006**: System MUST differentiate the currently active verse from upcoming or past verses through visual styling (highlighting, opacity changes, or color)
- **FR-007**: System MUST overlay metadata showing the Parasha name, Aliyah name, and current verse reference
- **FR-008**: System MUST process audio files that correspond to individual Aliyot (one Aliyah per audio file)
- **FR-010**: System MUST use legally permissible Hebrew text sources (open-source or appropriately licensed)
- **FR-011**: System MUST preserve attribution to the original audio source (Yoseph Joseph Bodenhaimer recordings)
- **FR-012**: System MUST handle Torah portions from the complete Hebrew Bible (all Parashot)

### Key Entities

- **Parasha**: A weekly Torah portion (e.g., "Haazinu", "Bereshit"). Contains multiple Aliyot. Identified by name and book/chapter/verse range.
- **Aliyah**: A subdivision of a Parasha, traditionally one of seven sections (Rishon, Sheni, Shlishi, Revi'i, Chamishi, Shishi, Shevi'i). Contains multiple verses. Associated with one audio file.
- **Pasuk (Verse)**: The atomic unit of synchronization. A single verse of Hebrew text with vowels and cantillation marks. Has a start timestamp and end timestamp within an audio file.
- **Haftara**: A weekly Nevieim portion that is Identified by name and book/chapter/verse range.
- **Audio Source**: A recording file (MP4/MP3/WAV) containing the recitation of one Aliyah. Sourced from Yoseph Joseph Bodenhaimer's recordings.
- **Hebrew Text Source**: Database or API providing vowelized Hebrew text with cantillation marks (e.g., Sefaria). Must be open-source or properly licensed.
- **Synchronized Video**: Output video file combining audio, Hebrew text display, verse highlighting, and metadata overlay.
- **Timestamp Map**: Data structure mapping each Pasuk to its precise start and end time in the audio, enabling synchronization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A viewer can follow along with the highlighted text and identify which verse is being read at any moment during playback without prior knowledge of the audio
- **SC-002**: Hebrew text rendering preserves all vowel points (Nikkud) and cantillation marks (T'amim) with sufficient clarity for reading practice (minimum readable font size on standard display)
- **SC-003**: Verse highlighting transitions occur within 0.5 seconds of the actual verse boundary in the audio (perceived as real-time synchronization)
- **SC-004**: Metadata (Parasha, Aliyah, verse reference) is visible and readable throughout the entire video playback
- **SC-005**: The system successfully processes and generates synchronized videos for at least one complete Parasha (with 7 Aliyot) as proof of scalability
- **SC-006**: Generated videos comply with copyright requirements (open-source text, proper attribution for audio)
- **SC-007**: Users can identify which Aliyah they are watching within 5 seconds of starting video playback
- **SC-008**: 95% of verse boundaries align accurately with the audio (allowing for minor timing variations due to reading style)

## Assumptions

- Audio files are already segmented by Aliyah (one audio file per Aliyah, not combined)
- Audio quality is sufficient for automated speech-to-text alignment (minimal background noise, clear pronunciation)
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
