# Verse Highlighting Visual Architecture

**Date**: 2026-03-07
**Purpose**: Visual explanation of multi-layer highlighting approach

---

## Current Implementation (Static)

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

---

## Proposed Implementation (Multi-Layer Highlighting)

### Layer Composition

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

---

## Rendering Pipeline

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

---

## Frame-by-Frame Example

### Scenario: 3 verses, 640×360 video

**Verse Data**:
- Verse 1: "האזינו השמים ואדברה" (0.0s - 4.2s)
- Verse 2: "יערף כמטר לקחי" (4.2s - 7.8s)
- Verse 3: "תזל כטל אמרתי" (7.8s - 11.5s)

### Frame at t=0.5s (during Verse 1)

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

Active Layers:
✅ Background (black)
✅ Normal layer - Verse 1 (white, BEHIND highlight)
✅ Normal layer - Verse 2 (white)
✅ Normal layer - Verse 3 (white)
✅ Highlight layer - Verse 1 (gold, OVER normal) ← Currently visible
❌ Highlight layer - Verse 2 (not started yet)
❌ Highlight layer - Verse 3 (not started yet)
```

### Frame at t=5.0s (during Verse 2)

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

Active Layers:
✅ Background (black)
✅ Normal layer - Verse 1 (white)
✅ Normal layer - Verse 2 (white, BEHIND highlight)
✅ Normal layer - Verse 3 (white)
❌ Highlight layer - Verse 1 (ended at t=4.2s)
✅ Highlight layer - Verse 2 (gold, OVER normal) ← Currently visible
❌ Highlight layer - Verse 3 (not started yet)
```

### Frame at t=9.0s (during Verse 3)

```
┌─────────────────────────────────────────┐
│ 640×360 Video Frame @ t=9.0s            │
│                                         │
│  (1) האזינו השמים ואדברה               │ ← White (completed)
│                                         │
│  (2) יערף כמטר לקחי                   │ ← White (completed)
│                                         │
│  ╔═══════════════════════════════════╗ │
│  ║ (3) תזל כטל אמרתי                ║ │ ← GOLD (highlighted)
│  ╚═══════════════════════════════════╝ │
│                                         │
└─────────────────────────────────────────┘

Active Layers:
✅ Background (black)
✅ Normal layer - Verse 1 (white)
✅ Normal layer - Verse 2 (white)
✅ Normal layer - Verse 3 (white, BEHIND highlight)
❌ Highlight layer - Verse 1 (ended)
❌ Highlight layer - Verse 2 (ended)
✅ Highlight layer - Verse 3 (gold, OVER normal) ← Currently visible
```

---

## Memory Layout

### Clip Objects in Memory

```
┌─────────────────────────────────────────────────────────┐
│  CompositeVideoClip                                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Background (ColorClip)                          │  │
│  │ - Resolution: 640×360                           │  │
│  │ - Color: (0, 0, 0) black                        │  │
│  │ - Duration: full video (e.g., 612s)             │  │
│  │ - Memory: ~100KB                                │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Normal Clips (6 verses × ~500KB each = 3MB)     │  │
│  │                                                 │  │
│  │  ├─ Verse 1 (ImageClip, white, t=0 to END)     │  │
│  │  ├─ Verse 2 (ImageClip, white, t=0 to END)     │  │
│  │  ├─ Verse 3 (ImageClip, white, t=0 to END)     │  │
│  │  ├─ Verse 4 (ImageClip, white, t=0 to END)     │  │
│  │  ├─ Verse 5 (ImageClip, white, t=0 to END)     │  │
│  │  └─ Verse 6 (ImageClip, white, t=0 to END)     │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Highlight Clips (6 verses × ~500KB = 3MB)       │  │
│  │                                                 │  │
│  │  ├─ Verse 1 (ImageClip, gold, t=0 to 4.2s)     │  │
│  │  ├─ Verse 2 (ImageClip, gold, t=4.2 to 8.1s)   │  │
│  │  ├─ Verse 3 (ImageClip, gold, t=8.1 to 12.3s)  │  │
│  │  ├─ Verse 4 (ImageClip, gold, t=12.3 to 16.5s) │  │
│  │  ├─ Verse 5 (ImageClip, gold, t=16.5 to 20.7s) │  │
│  │  └─ Verse 6 (ImageClip, gold, t=20.7 to 25.0s) │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Total Memory: ~6MB (well under 2GB target)            │
└─────────────────────────────────────────────────────────┘
```

### Scaling Analysis

```
Verses per Aliyah: 6-12 (typical)
Memory per verse (2 clips): ~1MB (500KB normal + 500KB highlight)

Typical Aliyah (8 verses):
  8 × 1MB = 8MB ✅ No problem

Long Aliyah (20 verses):
  20 × 1MB = 20MB ✅ Still fine

Very Long Aliyah (50 verses - edge case):
  50 × 1MB = 50MB ✅ Acceptable

Maximum (100 verses - extremely rare):
  100 × 1MB = 100MB ✅ Still under 2GB target
```

---

## Code Structure

### File: `src/services/text/hebrew_renderer.py`

```python
def render_verse_image(
    verse_num: int,
    hebrew_text: str,
    width: int,
    height: int,
    font_path: str,
    font_size: int,
    text_color: str = "#FFFFFF",  ← New parameter
    y_offset: int = 0,            ← New parameter
) -> Image.Image:
    """Render single verse with transparent background."""

    # Create RGBA image (transparent)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # ... RTL text processing ...
    # ... word wrapping ...

    # Draw at specified y_offset with specified color
    draw.multiline_text(
        (width - 20, y_offset),
        wrapped_text,
        font=font,
        fill=text_color,  ← Use provided color
        anchor="ra",
        align="right",
    )

    return image
```

### File: `src/services/video/renderer.py`

```python
def _create_text_clips(
    self,
    timestamp_map: TimestampMap,
    verses: list[tuple[str, str]],
    audio_duration: float,
) -> list:
    """Create multi-layer text clips with highlighting."""

    clips = []
    verse_spacing = 60  # pixels

    for i, (verse_timestamp, (ref, hebrew_text)) in enumerate(
        zip(timestamp_map.verse_timestamps, verses)
    ):
        y_offset = 20 + (i * verse_spacing)
        verse_num = int(ref.split(":")[-1])

        # LAYER 1: Normal (white, always visible)
        normal_image = render_verse_image(
            verse_num, hebrew_text, *self.resolution,
            self.font_path, self.font_size,
            text_color="#FFFFFF",  ← White
            y_offset=y_offset
        )
        normal_clip = self._image_to_clip(normal_image, audio_duration)
        clips.append(normal_clip)

        # LAYER 2: Highlight (gold, timed)
        highlight_image = render_verse_image(
            verse_num, hebrew_text, *self.resolution,
            self.font_path, self.font_size,
            text_color="#FFD700",  ← Gold
            y_offset=y_offset
        )
        highlight_clip = (
            self._image_to_clip(highlight_image, audio_duration)
            .with_start(verse_timestamp.start_time)
            .with_end(verse_timestamp.end_time)
        )
        clips.append(highlight_clip)

    return clips
```

---

## Testing Visualization

### Test Case: Single Verse Highlighting

```
Input:
  - Audio: 10 seconds
  - Verses: 3
  - Timestamps: [(0, 3.5), (3.5, 7.0), (7.0, 10.0)]

Expected Frame Colors:
  t=0.0s:  [GOLD] [white] [white]
  t=2.0s:  [GOLD] [white] [white]
  t=3.5s:  [white] [GOLD] [white]  ← Transition
  t=5.0s:  [white] [GOLD] [white]
  t=7.0s:  [white] [white] [GOLD]  ← Transition
  t=9.0s:  [white] [white] [GOLD]

Test Implementation:
  def test_highlight_timing():
      video = render(...)

      # Extract frames at key times
      frame_0 = video.get_frame(0.0)
      frame_3_5 = video.get_frame(3.5)
      frame_7_0 = video.get_frame(7.0)

      # Check color at verse 1 position (y=50)
      assert is_gold_color(frame_0, y=50)
      assert is_white_color(frame_3_5, y=50)
      assert is_white_color(frame_7_0, y=50)

      # Check color at verse 2 position (y=110)
      assert is_white_color(frame_0, y=110)
      assert is_gold_color(frame_3_5, y=110)
      assert is_white_color(frame_7_0, y=110)
```

---

## Future Enhancement: Scrolling

### Concept

```
┌─────────────────────────────────────────┐
│ Video Frame (Fixed 640×360 viewport)    │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Visible Area (scrolls up)       │   │
│  │                                 │   │
│  │  (4) verse 4                    │   │
│  │  ╔═══════════════════════════╗  │   │  ← Scrolling keeps
│  │  ║ (5) verse 5 (highlighted) ║  │   │    current verse
│  │  ╚═══════════════════════════╝  │   │    in center
│  │  (6) verse 6                    │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ▲                                      │
│  │ Canvas position moves up as verses   │
│  │ progress (verses 1-3 scrolled off)   │
│                                         │
└─────────────────────────────────────────┘
```

### Implementation (Phase 2)

```python
def get_scroll_position(t: float) -> int:
    """Calculate Y offset to keep current verse centered."""
    current_verse_idx = get_current_verse_index(t, timestamps)

    # Target: keep current verse at y=180 (center of 360px height)
    verse_y = 20 + (current_verse_idx * 60)  # Base verse position
    target_center_y = 180

    return target_center_y - verse_y

# Apply scrolling to entire text canvas
all_verses_clip = all_verses_clip.set_position(
    ('center', lambda t: get_scroll_position(t))
)
```

---

## Summary

**Approach**: Multi-layer composition with timed visibility

**Advantages**:
- ✅ Simple implementation (leverage moviepy's timing system)
- ✅ Clear visual hierarchy (highlight overlays normal)
- ✅ Low memory footprint (<50MB for typical Aliyah)
- ✅ Easy to test (can verify each layer independently)
- ✅ Easy to extend (add fade transitions, scrolling, etc.)

**Trade-offs**:
- Double memory usage (2 clips per verse) - but still acceptable
- No scrolling in Phase 1 (all verses must fit on screen)

**Next Steps**:
1. Implement `render_verse_image()` with color and y_offset parameters
2. Update `_create_text_clips()` to generate 2 layers per verse
3. Test with 3-verse sample
4. Validate timing accuracy
5. Scale to full Aliyot

---

**Generated by Claude Sonnet 4.5**
