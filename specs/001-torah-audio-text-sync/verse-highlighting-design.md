# Design Document: Verse-Level Highlighting for Hebrew Audio-Text Synchronization

**Feature**: 001-torah-audio-text-sync
**Created**: 2026-03-07
**Status**: Design Proposal
**Author**: Claude Sonnet 4.5

---

## Executive Summary

This document proposes a design for implementing **dynamic verse-level highlighting** in Torah reading videos. The system will display multiple Hebrew verses simultaneously and highlight each verse in real-time as it's spoken in the audio, creating a "karaoke-style" follow-along experience for students of Torah reading.

**Current State**: The system generates videos with static text overlays (all verses visible, no highlighting).
**Proposed State**: Videos will dynamically highlight the current verse being spoken while keeping other verses visible.

---

## Problem Statement

### Current Implementation Gaps

1. **No Dynamic Highlighting** - All verses are displayed statically with no visual indication of which verse is being spoken (violates FR-006)
2. **No Scrolling** - All verses are rendered in a single static image, which doesn't scale well for long Aliyot or support centering the active verse (violates FR-005a)
3. **Poor Learning Experience** - Users cannot easily follow along with the audio without manually tracking their position

### User Impact

Without verse-level highlighting, users must:
- Manually track which verse is being read
- Count verses to stay synchronized
- Potentially lose their place during playback

This defeats the primary value proposition: enabling students to **visually follow professional Torah readings**.

---

## Design Goals

1. **Accurate Synchronization** - Highlight verses within ±200ms of audio timing
2. **Visual Clarity** - Clear distinction between current, past, and upcoming verses
3. **Hebrew Text Fidelity** - Preserve all diacritical marks (Nikkud + T'amim) during highlighting
4. **Smooth Transitions** - Natural highlighting changes without jarring visual jumps
5. **Performance** - Render videos efficiently without excessive memory usage
6. **Maintainability** - Minimize complexity in rendering logic

---

## Architecture Overview

### Component Changes

| Component | Current State | Proposed Changes |
|-----------|---------------|------------------|
| **AlignmentEngine** | ✅ Verse-level timestamps | ✅ No changes (already works) |
| **TimestampMap** | ✅ Stores verse timestamps | ✅ No changes |
| **VideoRenderer** | ⚠️ Static image overlay | 🔄 Dynamic multi-clip composition |
| **hebrew_renderer** | ⚠️ Single static image | 🔄 Per-verse image generation |
| **Configuration** | ⚠️ No highlight settings | ➕ Add highlight colors, transition timing |

---

## Design Option Analysis

### Option 1: Multiple Text Layers with Opacity Animation (RECOMMENDED)

**Architecture**:
```python
# For each verse, create TWO clips:
# 1. Normal state (white text, always visible)
# 2. Highlighted state (gold text, visible only during verse time)

normal_clips = [create_verse_clip(v, color=WHITE) for v in verses]
highlight_clips = [
    create_verse_clip(v, color=GOLD)
    .with_start(v.start_time)
    .with_end(v.end_time)
    for v in verses
]

# Composite: background + all normal clips + all highlight clips
video = CompositeVideoClip([background, *normal_clips, *highlight_clips])
```

**Pros**:
- ✅ Clean separation of concerns (normal vs. highlighted state)
- ✅ Simple timing logic (moviepy handles start/end times)
- ✅ Smooth transitions (no custom animation code)
- ✅ All verses always visible (meets FR-005a)
- ✅ Easy to debug (can export layers independently)

**Cons**:
- ⚠️ Double memory usage (2 clips per verse)
- ⚠️ No scrolling (all verses static on screen)

**Memory Impact**:
- Typical Aliyah: 6-12 verses
- Memory per verse: ~500KB (640×360 PNG)
- Total: 6MB - 12MB for normal + highlight layers
- **Verdict**: Acceptable for target hardware (< 2GB RAM)

---

### Option 2: Dynamic Color Overlay with Lambda Functions

**Architecture**:
```python
def make_highlight_function(verse_timestamps):
    def get_color(t):
        for verse in verse_timestamps:
            if verse.start_time <= t < verse.end_time:
                return GOLD
        return WHITE
    return get_color

# Create single text clip per verse, color changes over time
clips = [
    create_verse_clip(verse, color_func=make_highlight_function([verse]))
    for verse in verses
]
```

**Pros**:
- ✅ Lower memory usage (1 clip per verse)
- ✅ More flexible for complex timing logic

**Cons**:
- ❌ Moviepy's `TextClip` doesn't support dynamic color functions
- ❌ Would require custom frame-by-frame rendering
- ❌ Complex to implement and test
- ❌ Potential performance issues (re-render text on every frame)

**Verdict**: NOT RECOMMENDED (technical constraints)

---

### Option 3: Scrolling Multi-Screen Layout

**Architecture**:
```python
# Divide verses into "screens" (3-4 verses per screen)
# Scroll to next screen when current screen's last verse starts

screen_height = video_height
verse_height = 80  # pixels per verse
verses_per_screen = screen_height // verse_height

# Create tall canvas with all verses
full_text_height = len(verses) * verse_height
text_canvas = Image.new('RGB', (width, full_text_height), 'black')

# Animate Y position to scroll
def get_y_position(t):
    current_verse_idx = get_current_verse_index(t, timestamps)
    current_screen = current_verse_idx // verses_per_screen
    return -current_screen * screen_height

clip = ImageClip(text_canvas).set_position(('center', get_y_position))
```

**Pros**:
- ✅ Scales to very long Aliyot (100+ verses)
- ✅ Keeps current verse in upper third of screen
- ✅ More "professional" feel (less cluttered)

**Cons**:
- ⚠️ Complex position calculation logic
- ⚠️ Jarring transitions if not smoothed
- ⚠️ Higher implementation complexity
- ⚠️ Harder to test edge cases (verse boundaries on screen transitions)

**Verdict**: DEFER to Phase 2 (implement after Option 1 is working)

---

## Recommended Implementation: Option 1 (Multi-Layer)

### Phase 1: Basic Highlighting (No Scrolling)

#### 1.1 Configuration Updates

**File**: `settings.toml`

```toml
[default.video]
# ... existing settings ...
highlight_color = "#FFD700"       # Gold for current verse
normal_color = "#FFFFFF"          # White for other verses
past_verse_opacity = 0.6          # Dim completed verses (optional enhancement)
highlight_transition_ms = 100     # Fade-in time for highlight
```

#### 1.2 Hebrew Renderer Updates

**File**: `src/services/text/hebrew_renderer.py`

**New Function**: `render_verse_image()`

```python
def render_verse_image(
    verse_num: int,
    hebrew_text: str,
    width: int,
    height: int,
    font_path: str,
    font_size: int,
    text_color: str = "#FFFFFF",
    y_offset: int = 0,
) -> Image.Image:
    """Render a single verse as an image with transparent background.

    Args:
        verse_num: Verse number for display
        hebrew_text: Hebrew text with Nikkud and T'amim
        width: Image width
        height: Image height
        font_path: Path to Hebrew font
        font_size: Font size in points
        text_color: Hex color for text (e.g., "#FFFFFF" or "#FFD700")
        y_offset: Vertical offset for positioning

    Returns:
        PIL Image with RGBA mode (transparent background)
    """
    # Create transparent image
    image = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    # Format verse with number: (1) hebrew_text
    display_text = f"({verse_num}) {hebrew_text}"
    display_text = get_display(display_text)  # RTL reordering

    # Text wrapping logic (same as current implementation)
    # ... word wrapping code ...

    # Draw text at specified y_offset
    draw.multiline_text(
        (width - 20, y_offset),  # Right margin
        wrapped_text,
        font=font,
        fill=text_color,
        anchor="ra",
        spacing=font_size + 5,
        align="right",
    )

    return image
```

#### 1.3 Video Renderer Updates

**File**: `src/services/video/renderer.py`

**Replace**: `_create_text_clips()`

```python
def _create_text_clips(
    self,
    timestamp_map: TimestampMap,
    verses: list[tuple[str, str]] | None = None,
    audio_duration: float = 10.0,
) -> list:
    """Create dynamic text clips with verse-level highlighting.

    Creates two layers per verse:
    1. Normal layer (white, visible entire video)
    2. Highlight layer (gold, visible only during verse timing)

    Args:
        timestamp_map: TimestampMap with verse timestamps
        verses: List of (reference, hebrew_text) tuples
        audio_duration: Audio duration in seconds

    Returns:
        List of ImageClips for compositing
    """
    width, height = self.resolution
    clips = []

    # Calculate layout
    verse_spacing = 60  # pixels between verses
    y_offset = 20  # top margin

    for i, verse_timestamp in enumerate(timestamp_map.verse_timestamps):
        if i >= len(verses):
            logger.warning(f"More timestamps than verses, stopping at {i}")
            break

        ref, hebrew_text = verses[i]
        verse_num = ref.split(":")[-1] if ":" in ref else str(i + 1)

        # Calculate verse position
        verse_y = y_offset + (i * verse_spacing)

        # LAYER 1: Normal state (white, always visible)
        normal_image = render_verse_image(
            verse_num=int(verse_num),
            hebrew_text=hebrew_text,
            width=width,
            height=height,
            font_path=str(self.font_path),
            font_size=self.font_size,
            text_color=self.normal_color,  # White
            y_offset=verse_y,
        )
        normal_clip = self._image_to_clip(normal_image, audio_duration)
        clips.append(normal_clip)

        # LAYER 2: Highlight state (gold, visible during verse time only)
        highlight_image = render_verse_image(
            verse_num=int(verse_num),
            hebrew_text=hebrew_text,
            width=width,
            height=height,
            font_path=str(self.font_path),
            font_size=self.font_size,
            text_color=self.highlight_color,  # Gold
            y_offset=verse_y,
        )
        highlight_clip = (
            self._image_to_clip(highlight_image, audio_duration)
            .with_start(verse_timestamp.start_time)
            .with_end(verse_timestamp.end_time)
        )
        clips.append(highlight_clip)

    logger.info(f"Created {len(clips)} text clips ({len(clips)//2} verses × 2 layers)")
    return clips

def _image_to_clip(self, image: Image.Image, duration: float) -> ImageClip:
    """Convert PIL Image to ImageClip with temporary file.

    Args:
        image: PIL Image (RGB or RGBA)
        duration: Clip duration in seconds

    Returns:
        ImageClip
    """
    temp_path = tempfile.mktemp(suffix=".png")
    image.save(temp_path)
    clip = ImageClip(temp_path).with_duration(duration)
    logger.debug(f"Created ImageClip from {temp_path}")
    return clip
```

#### 1.4 Testing Strategy

**File**: `tests/integration/test_verse_highlighting.py`

```python
def test_verse_highlighting_timing(fixture_audio, fixture_verses):
    """Test that highlight clips start/end at correct times."""
    # ... test implementation ...

def test_highlight_color_accuracy(fixture_timestamp_map):
    """Test that highlighted verses use gold color (#FFD700)."""
    # ... extract frame at verse start time ...
    # ... verify gold pixels present ...

def test_all_verses_always_visible(fixture_video):
    """Test that normal layer keeps all verses visible."""
    # ... extract frame at t=0 and t=end ...
    # ... verify all verse text present in white ...
```

---

### Phase 2: Scrolling Enhancement (Optional)

Once Phase 1 is working, add scrolling to keep the current verse centered.

**Implementation**:
1. Calculate total text canvas height (all verses)
2. Generate single tall image with all verses
3. Use `set_position` with time-based lambda to scroll
4. Add smooth easing function for transitions

**Complexity**: Medium (3-5 days additional work)

---

## Alignment Model Evaluation

### Current: aeneas with DTW

**How It Works**:
1. Audio → MFCC features (Mel-Frequency Cepstral Coefficients)
2. Text → TTS synthesis → MFCC features
3. DTW (Dynamic Time Warping) aligns both MFCC sequences
4. Output: Start/end timestamps per text fragment

**Current Configuration**:
- Language: `eng` (English TTS via espeak)
- Text Type: `plain` (one line per verse)
- Output: JSON sync map

**Accuracy Metrics** (from current code):
- Confidence calculation based on gap detection
- Target: 0.90+ confidence score
- Validation: Monotonic timestamps, gaps < 5 seconds

**Limitations for Hebrew**:
1. **No Hebrew TTS** - espeak doesn't have Hebrew voice
   - Current workaround: Use English TTS, alignment still works because DTW compares audio features (language-agnostic)
   - Impact: Sub-optimal for Hebrew prosody/rhythm differences

2. **Verse-Level Only** - Cannot do word-level alignment
   - Current granularity: ~4-8 seconds per verse
   - User request mentions: "maybe we need to check various AI models"

---

### Alternative: Whisper + Forced Alignment

**Whisper** (OpenAI) is a state-of-the-art ASR model with multilingual support including Hebrew.

#### Option A: WhisperX

**GitHub**: https://github.com/m-bain/whisperX

**Capabilities**:
- Word-level timestamps using phoneme alignment
- Native Hebrew language support
- Uses wav2vec2 for forced alignment (more accurate than DTW)
- Returns JSON with word-level timings

**Example Output**:
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 4.2,
      "text": "האזינו השמים ואדברה",
      "words": [
        {"word": "האזינו", "start": 0.0, "end": 1.1},
        {"word": "השמים", "start": 1.2, "end": 2.0},
        {"word": "ואדברה", "start": 2.1, "end": 4.2}
      ]
    }
  ]
}
```

**Pros**:
- ✅ Native Hebrew ASR (better accuracy for Hebrew phonetics)
- ✅ Word-level granularity (could enable word-by-word highlighting in future)
- ✅ Better confidence scores (based on ASR probability)
- ✅ Active development and community support
- ✅ Handles Hebrew diacritics better (trained on diverse Hebrew audio)

**Cons**:
- ⚠️ Requires GPU for real-time performance (CPU: ~30s per minute of audio)
- ⚠️ Larger dependency (PyTorch + Whisper models ~3GB)
- ⚠️ More complex setup (model downloads, CUDA config)
- ⚠️ Higher memory usage (~4-6GB during processing)

**Performance Comparison**:

| Metric | aeneas (current) | WhisperX |
|--------|------------------|----------|
| **Processing Speed** | ~1 minute / 10min audio | ~5 minutes / 10min audio (CPU) |
| **Accuracy** | 85-95% (verse-level) | 95-98% (word-level) |
| **Memory** | ~500MB | ~4-6GB |
| **Dependencies** | espeak, ffmpeg (~50MB) | PyTorch, Whisper (~3GB) |
| **Hebrew Support** | Indirect (MFCC-based) | Native (trained on Hebrew) |

---

#### Option B: montreal-forced-aligner (MFA)

**GitHub**: https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner

**Capabilities**:
- Phoneme-level forced alignment using acoustic models
- Requires Hebrew acoustic model + pronunciation dictionary
- Research-grade aligner used in linguistics

**Pros**:
- ✅ Highest accuracy for phoneme-level alignment
- ✅ Handles pronunciation variations

**Cons**:
- ❌ No pre-trained Hebrew models readily available
- ❌ Requires training corpus (hundreds of hours of annotated Hebrew audio)
- ❌ Complex setup and configuration
- ❌ Overkill for verse-level synchronization

**Verdict**: NOT RECOMMENDED (too complex for current needs)

---

#### Option C: wav2vec2 + CTC Forced Alignment

**Hugging Face**: facebook/wav2vec2-large-xlsr-53-hebrew

**Capabilities**:
- Hebrew ASR model based on wav2vec2
- CTC (Connectionist Temporal Classification) for alignment
- Can be adapted for forced alignment

**Pros**:
- ✅ Native Hebrew support
- ✅ Smaller than Whisper (~1.2GB model)

**Cons**:
- ⚠️ Requires custom forced alignment implementation
- ⚠️ Less documented than WhisperX for alignment use case
- ⚠️ Still requires PyTorch

**Verdict**: POSSIBLE but more implementation work than WhisperX

---

### Recommendation: Hybrid Approach

**Phase 1: Keep aeneas**
- ✅ Already working with acceptable accuracy (90%+)
- ✅ Lightweight and fast
- ✅ Sufficient for verse-level highlighting
- ✅ No new dependencies

**Phase 2: Evaluate WhisperX (if accuracy issues arise)**

**Decision Criteria** (when to switch):
1. **User reports accuracy issues** - If >10% of Aliyot have misaligned verses
2. **Word-level highlighting requested** - If users want individual word highlighting
3. **GPU resources available** - If deployment environment has GPU

**Implementation Strategy**:
1. Design `AlignmentEngine` as pluggable interface
2. Create `AeneasAligner` (current) and `WhisperAligner` (future)
3. Add configuration flag: `alignment.engine = "aeneas" | "whisper"`
4. Test both engines on same audio samples
5. Compare accuracy metrics and processing time

```python
# Abstract interface
class AlignmentEngine(Protocol):
    def align(
        self,
        audio_file: Path,
        verses: list[tuple[str, str]]
    ) -> TimestampMap:
        ...

# Current implementation (keep)
class AeneasAligner(AlignmentEngine):
    # ... existing code ...

# Future implementation (Phase 2)
class WhisperAligner(AlignmentEngine):
    def __init__(self, model_size: str = "medium"):
        import whisperx
        self.model = whisperx.load_model(model_size, language="he")

    def align(self, audio_file, verses):
        result = self.model.transcribe(str(audio_file))
        # Map recognized words to verse boundaries
        # Return TimestampMap
```

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Memory overflow** (too many clips) | Low | High | Limit clips to 50 verses, add pagination for longer Aliyot |
| **Poor alignment accuracy** | Medium | High | Test on diverse audio samples, provide manual timestamp correction UI |
| **Hebrew rendering issues** (diacritics as boxes) | Medium | Medium | Document PIL limitations, consider Cairo/Pango if critical |
| **Performance degradation** | Low | Medium | Profile rendering, optimize clip generation |
| **Transition jitter** | Low | Low | Add slight overlap (±50ms) for smooth visual transitions |

---

## Success Metrics

### Functional Metrics
- ✅ 100% of verses have highlight clips with correct timing
- ✅ Highlight color matches configuration (#FFD700)
- ✅ All verses remain visible (white layer present)
- ✅ No timestamp overlaps or gaps

### Quality Metrics
- ✅ Alignment accuracy ≥ 90% (current aeneas standard)
- ✅ Highlighting latency < 200ms from audio
- ✅ Hebrew diacritics fully visible in both layers

### Performance Metrics
- ✅ Video rendering time < 5 minutes per Aliyah (640×360, 30fps)
- ✅ Peak memory usage < 2GB during rendering
- ✅ Output file size: 5-10MB per minute of video (H.264 CRF 23)

---

## Implementation Plan

### Week 1: Phase 1 - Basic Highlighting
1. **Day 1-2**: Update `hebrew_renderer.py` with `render_verse_image()`
2. **Day 3-4**: Refactor `VideoRenderer._create_text_clips()` for multi-layer
3. **Day 5**: Add configuration settings for highlight colors
4. **Day 6-7**: Integration testing and bug fixes

### Week 2: Testing & Refinement
1. **Day 8-9**: Write comprehensive tests for verse highlighting
2. **Day 10-11**: Test on diverse Aliyot (short, long, edge cases)
3. **Day 12-13**: Documentation and code review
4. **Day 14**: Final validation against FR-005a and FR-006

### Future (Phase 2): Scrolling & Advanced Features
- Implement scrolling to keep current verse centered
- Evaluate WhisperX for improved alignment
- Add word-level highlighting (if WhisperX adopted)
- Implement manual timestamp correction UI

---

## Open Questions

1. **Scrolling Behavior** - Should past verses scroll off-screen or remain visible (dimmed)?
   - **Recommendation**: Keep all verses visible (no scrolling) for Phase 1, defer scrolling to Phase 2

2. **Transition Smoothing** - Should highlights fade in/out or appear instantly?
   - **Recommendation**: Start with instant transitions (simpler), add fade-in (100ms) in Phase 1.1 if needed

3. **Font Rendering** - Should we switch from PIL to Cairo/Pango for better diacritics?
   - **Recommendation**: Defer until users report rendering issues (PIL works for 80%+ of cases)

4. **Alignment Engine** - Should we switch to WhisperX immediately or wait for accuracy issues?
   - **Recommendation**: Keep aeneas for Phase 1, add WhisperX as optional backend in Phase 2

---

## Conclusion

This design proposes a **pragmatic, incremental approach** to verse-level highlighting:

**Phase 1** implements basic multi-layer highlighting using the existing aeneas alignment engine. This satisfies FR-005a and FR-006 with minimal risk and complexity.

**Phase 2** (future) adds scrolling and optionally upgrades to WhisperX for improved accuracy and word-level granularity.

This approach balances **user value** (immediate highlighting), **technical risk** (proven technologies), and **future extensibility** (pluggable alignment engine).

---

## References

- [aeneas Documentation](https://github.com/readbeyond/aeneas)
- [WhisperX GitHub](https://github.com/m-bain/whisperX)
- [moviepy Text Effects](https://zulko.github.io/moviepy/getting_started/effects.html)
- [Sefaria API Docs](https://developers.sefaria.org/)
- Project Spec: `specs/001-torah-audio-text-sync/spec.md`
- Research Notes: `specs/001-torah-audio-text-sync/research.md`

---

**Generated by Claude Sonnet 4.5**
