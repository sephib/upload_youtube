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

> **Full comparison**: See [alignment-model-comparison.md](alignment-model-comparison.md) for detailed
> evaluation of aeneas, WhisperX, MFA, and wav2vec2.

**Decision**: Keep aeneas for Phase 1 (verse-level highlighting). Evaluate WhisperX in Phase 2
if accuracy issues arise or word-level highlighting is requested.

**Key factors for this design**:
- aeneas is sufficient for verse-level granularity (90%+ accuracy)
- No GPU required, minimal dependencies
- `AlignmentEngine` is designed as a pluggable Protocol to support future alternatives

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
- Alignment Model Comparison: `specs/001-torah-audio-text-sync/alignment-model-comparison.md`

---

## Appendix: Visual Architecture Diagrams

<!-- Consolidated from verse-highlighting-diagram.md -->

### Current Implementation (Static)

```
┌─────────────────────────────────────────┐
│  Video Frame (t = any time)             │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Black Background                 │ │
│  │                                   │ │
│  │  (1) verse 1 text ────────────┐  │ │
│  │  (2) verse 2 text             │  │ │
│  │  (3) verse 3 text             │  │ │  ← All verses
│  │  (4) verse 4 text             │  │ │    white, static,
│  │  (5) verse 5 text             │  │ │    always visible
│  │  (6) verse 6 text ────────────┘  │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘

Problem: No indication of which verse is being spoken
```

### Proposed Layer Composition

```
┌─────────────────────────────────────────────────────────┐
│  Composite Video                                        │
│                                                         │
│  Layer 1: Background (Black) ──────────────────┐       │
│  Layer 2: Normal Text (White)                  │       │
│  Layer 3: Highlight Text (Gold) ────────────┐  │       │
│                                              │  │       │
│  ┌─────────────────────────────────────┐    │  │       │
│  │                                     │    │  │       │
│  │  (1) verse 1 ───┐                  │    │  │       │
│  │  (2) verse 2    │ ← Normal layer   │    │  │       │
│  │  (3) verse 3 ───┘   (white, always │    │  │       │
│  │  (4) verse 4        visible)        │    │  │       │
│  │  (5) verse 5                        │    │  │       │
│  │  (6) verse 6                        │    │  │       │
│  │         ↑                           │    │  │       │
│  │         └── Highlight layer ────────┘    │  │       │
│  │             (gold, visible only          │  │       │
│  │              during verse time)          │  │       │
│  │                                          │  │       │
│  └──────────────────────────────────────────┘  │       │
│                                                 │       │
└─────────────────────────────────────────────────┘       │
```

### Timeline View

```
Time:  0s    1s    2s    3s    4s    5s    6s    7s    8s
       │     │     │     │     │     │     │     │     │
Verse 1: [════════════════]
         └─ Normal layer: white, t=0 to t=END
         └─ Highlight layer: gold, t=0 to t=4.2

Verse 2:                  [════════════════]
                          └─ Normal: white, t=0 to t=END
                          └─ Highlight: gold, t=4.2 to t=8.1

Verse 3:                                      [═══════...
                                              └─ Normal: white
                                              └─ Highlight: gold, t=8.1+

Visual Result:
0-4.2s:  Verse 1 GOLD, Verse 2 white, Verse 3 white
4.2-8.1s: Verse 1 white, Verse 2 GOLD, Verse 3 white
8.1+s:   Verse 1 white, Verse 2 white, Verse 3 GOLD
```

### Rendering Pipeline

```
┌───────────────────────────────────────────────────────────────┐
│  Input: TimestampMap + Verses                                 │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────┐
│  Step 1: Generate Normal Layer Images                         │
│                                                                │
│  for each verse:                                               │
│    image = render_verse_image(                                │
│      verse_num, hebrew_text,                                  │
│      color="#FFFFFF",  ← White                                │
│      y_offset = i * verse_spacing                             │
│    )                                                           │
│    clip = ImageClip(image).with_duration(full_video_duration) │
│    normal_clips.append(clip)                                  │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────┐
│  Step 2: Generate Highlight Layer Images                      │
│                                                                │
│  for each verse, timestamp:                                   │
│    image = render_verse_image(                                │
│      verse_num, hebrew_text,                                  │
│      color="#FFD700",  ← Gold                                 │
│      y_offset = i * verse_spacing                             │
│    )                                                           │
│    clip = ImageClip(image)                                    │
│      .with_start(timestamp.start_time)  ← Only visible during │
│      .with_end(timestamp.end_time)      ← verse audio time    │
│    highlight_clips.append(clip)                               │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────┐
│  Step 3: Composite All Layers                                 │
│                                                                │
│  video = CompositeVideoClip([                                 │
│    black_background,                                          │
│    *normal_clips,     ← All verses (white, always visible)    │
│    *highlight_clips   ← Current verse (gold, timed)           │
│  ])                                                            │
│  video = video.with_audio(audio_clip)                         │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────────────┐
│  Output: MP4 Video (640×360, 30fps, H.264)                    │
└───────────────────────────────────────────────────────────────┘
```

### Frame-by-Frame Example

**Scenario**: 3 verses, 640x360 video

**Verse Data**:
- Verse 1: "האזינו השמים ואדברה" (0.0s - 4.2s)
- Verse 2: "יערף כמטר לקחי" (4.2s - 7.8s)
- Verse 3: "תזל כטל אמרתי" (7.8s - 11.5s)

**Frame at t=0.5s (during Verse 1)**:

```
┌─────────────────────────────────────────┐
│ 640×360 Video Frame @ t=0.5s            │
│                                         │
│  ╔═══════════════════════════════════╗ │
│  ║ (1) האזינו השמים ואדברה          ║ │ ← GOLD (highlighted)
│  ╚═══════════════════════════════════╝ │
│                                         │
│  (2) יערף כמטר לקחי                   │ ← White (normal)
│                                         │
│  (3) תזל כטל אמרתי                    │ ← White (normal)
│                                         │
└─────────────────────────────────────────┘
```

**Frame at t=5.0s (during Verse 2)**:

```
┌─────────────────────────────────────────┐
│ 640×360 Video Frame @ t=5.0s            │
│                                         │
│  (1) האזינו השמים ואדברה               │ ← White (completed)
│                                         │
│  ╔═══════════════════════════════════╗ │
│  ║ (2) יערף כמטר לקחי               ║ │ ← GOLD (highlighted)
│  ╚═══════════════════════════════════╝ │
│                                         │
│  (3) תזל כטל אמרתי                    │ ← White (upcoming)
│                                         │
└─────────────────────────────────────────┘
```

### Memory Layout and Scaling

```
Clip Objects in Memory:
  CompositeVideoClip
  ├── Background (ColorClip): 640×360, black, ~100KB
  ├── Normal Clips (6 verses × ~500KB = 3MB)
  │   ├── Verse 1 (ImageClip, white, t=0 to END)
  │   ├── Verse 2-5 ...
  │   └── Verse 6 (ImageClip, white, t=0 to END)
  └── Highlight Clips (6 verses × ~500KB = 3MB)
      ├── Verse 1 (ImageClip, gold, t=0 to 4.2s)
      ├── Verse 2-5 ...
      └── Verse 6 (ImageClip, gold, t=20.7 to 25.0s)

Scaling Analysis:
  Typical Aliyah (8 verses):  8 × 1MB = 8MB
  Long Aliyah (20 verses):   20 × 1MB = 20MB
  Very Long (50 verses):     50 × 1MB = 50MB
  All well under 2GB target.
```

---

**Generated by Claude Sonnet 4.5**
<!-- Edited by Claude Opus 4.6 - consolidated verse-highlighting-diagram.md -->
