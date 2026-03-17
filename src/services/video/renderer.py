# Edited by Claude Code, Claude Opus 4.6 (updated for PasukAlignment model)
"""VideoRenderer for creating synchronized videos with Hebrew text overlay."""

import tempfile
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
)
from PIL import Image

from src.lib.config import get_font_path, settings
from src.lib.exceptions import VideoRenderError
from src.lib.logging import get_logger
from src.models.alignment_run import AlignmentRun
from src.models.alya_video import AlyaVideo
from src.models.pasuk_alignment import PasukAlignment
from src.services.text.hebrew_renderer import (
    render_hebrew_text_image_simple,
    render_verse_image,
    render_verses_tall_canvas,
)

logger = get_logger(__name__)


class VideoRenderer:
    """Renderer for synchronized Torah reading videos with text overlay.

    Creates MP4 videos with scrolling Hebrew text that highlights in sync
    with audio playback.
    """

    def __init__(
        self,
        resolution: tuple[int, int] | None = None,
        fps: int | None = None,
        font_path: Path | None = None,
    ) -> None:
        """Initialize video renderer.

        Args:
            resolution: Video resolution (width, height) - default from config
            fps: Frames per second - default from config
            font_path: Path to Hebrew font - default from config
        """
        self.resolution = tuple(resolution) if resolution else tuple(
            settings.get("video.resolution", [640, 360])
        )
        self.fps = fps or settings.get("video.fps", 30)
        self.font_path = font_path or get_font_path()
        self.font_size = settings.get("video.font_size", 20)
        self.highlight_color = settings.get("video.highlight_color", "#FFD700")
        self.normal_color = settings.get("video.normal_color", "#FFFFFF")

        logger.debug(
            f"Initialized VideoRenderer",
            resolution=self.resolution,
            fps=self.fps,
            font_path=str(self.font_path),
        )

    def render(
        self,
        audio_file: Path,
        alignment_run: AlignmentRun,
        output_path: Path,
        verses: list[tuple[str, str]] | None = None,
        pasuk_alignments: list[PasukAlignment] | None = None,
        alya_id: int | None = None,
    ) -> AlyaVideo:
        """Render synchronized video with text overlay.

        Args:
            audio_file: Path to audio file
            alignment_run: AlignmentRun with verse timestamps
            output_path: Output video file path
            verses: Optional list of (reference, hebrew_text) tuples
            pasuk_alignments: Per-verse alignment data
            alya_id: FK to alyot.id (passed from pipeline)

        Returns:
            AlyaVideo model

        Raises:
            VideoRenderError: If rendering fails
        """
        verse_count = len(pasuk_alignments) if pasuk_alignments else 0
        logger.info(
            f"Starting video render",
            audio_file=str(audio_file),
            verse_count=verse_count,
            output_path=str(output_path),
        )

        try:
            # Load audio
            audio_clip = AudioFileClip(str(audio_file))
            duration = audio_clip.duration

            # Create background
            background = ColorClip(
                size=self.resolution, color=(0, 0, 0), duration=duration
            )  # Black background

            # Create text clips for each verse
            text_clips = self._create_text_clips(alignment_run, verses, duration, pasuk_alignments)

            # Composite video
            video = CompositeVideoClip([background] + text_clips)
            video = video.with_audio(audio_clip)
            video = video.with_fps(self.fps)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Render video
            logger.info(f"Encoding video", codec="libx264", bitrate="1000k")
            video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=self.fps,
                preset="medium",
                bitrate="1000k",
                logger=None,  # Suppress moviepy's verbose logging
            )

            # Clean up
            audio_clip.close()
            video.close()

            # Validate output
            if not output_path.exists():
                raise VideoRenderError(f"Video file was not created: {output_path}")

            logger.info(
                f"Video rendered successfully",
                output_path=str(output_path),
                file_size_mb=output_path.stat().st_size / (1024 * 1024),
            )

            # Create AlyaVideo model
            return AlyaVideo(
                alya_id=alya_id or 0,  # TODO: pass alya_id from pipeline, not from alignment_run
                file_path=str(output_path),
                format="mp4",
                resolution_w=self.resolution[0],
                resolution_h=self.resolution[1],
                frame_rate=self.fps,
                codec="h264",
                duration_seconds=duration,
            )

        except Exception as e:
            raise VideoRenderError(f"Video rendering failed: {e}") from e

    def _create_text_clips(
        self,
        alignment_run: AlignmentRun,
        verses: list[tuple[str, str]] | None = None,
        audio_duration: float = 10.0,
        pasuk_alignments: list[PasukAlignment] | None = None,
    ) -> list:
        """Create dynamic text clips with verse-level highlighting.

        Automatically chooses between static and scrolling layout based on verse count:
        - <= 6 verses: Static layout (all verses visible, dual-layer highlighting)
        - > 6 verses: Scrolling layout (tall canvas with dynamic Y-offset)

        Creates two layers per verse:
        1. Normal layer (white, visible entire video)
        2. Highlight layer (gold, visible only during verse timing)

        This enables karaoke-style follow-along highlighting where the current
        verse is highlighted in gold while other verses remain white.

        Args:
            alignment_run: AlignmentRun with verse timestamps
            verses: Optional list of (reference, hebrew_text) tuples
            audio_duration: Audio duration in seconds
            pasuk_alignments: Optional list of PasukAlignment with timestamps

        Returns:
            List of ImageClips for compositing (normal layers + highlight layers)
        """
        if not verses:
            logger.warning("No verses provided, returning empty clip list")
            return []

        # Use scrolling layout for > 6 verses to prevent overflow
        if len(verses) > 6 and pasuk_alignments:
            logger.info(
                f"{len(verses)} verses detected (> 6), using scrolling layout"
            )
            return self._create_scrolling_text_clips(
                verses=verses,
                pasuk_alignments=pasuk_alignments,
                audio_duration=audio_duration,
            )

        # Static layout for <= 6 verses
        logger.info(f"{len(verses)} verses detected (<= 6), using static layout")
        width, height = self.resolution
        clips = []

        # Calculate layout - scale spacing proportionally to resolution
        scale = height / 360
        verse_spacing = int(60 * scale)  # pixels between verses
        y_offset = int(20 * scale)  # top margin

        logger.info(f"Creating dual-layer clips for {len(verses)} verses")

        for i, (ref, hebrew_text) in enumerate(verses):
            # Extract verse number from reference
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

            logger.debug(f"Created normal layer for verse {i+1}: {ref}")

            # LAYER 2: Highlight state (gold, visible only during verse time)
            if pasuk_alignments and i < len(pasuk_alignments):
                pasuk = pasuk_alignments[i]
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
                    .with_start(pasuk.start_time)
                    .with_end(pasuk.end_time)
                )
                clips.append(highlight_clip)

                logger.debug(
                    f"Created highlight layer for verse {i+1}: {ref}, "
                    f"t={pasuk.start_time:.2f}s to {pasuk.end_time:.2f}s"
                )

        logger.info(f"Created {len(clips)} text clips ({len(verses)} verses × 2 layers)")

        return clips

    def _create_scrolling_text_clips(
        self,
        verses: list[tuple[str, str]],
        pasuk_alignments: list[PasukAlignment],
        audio_duration: float,
    ) -> list:
        """Create scrolling text clips with verse highlighting.

        Implements centered scrolling where the current highlighted verse
        is kept in the upper third of the screen. Uses a tall canvas approach
        with dynamic Y-offset positioning.

        Strategy:
        - Layer 1: Normal canvas (scrolling, white text, always visible)
        - Layer 2: Highlight canvases (scrolling, gold text, time-synced per verse)

        Args:
            verses: List of (reference, hebrew_text) tuples
            pasuk_alignments: List of PasukAlignment with timestamps
            audio_duration: Audio duration in seconds

        Returns:
            List of ImageClips for compositing (1 normal + N highlight layers)
        """
        width, height = self.resolution
        clips = []

        if not verses or not pasuk_alignments:
            logger.warning("No verses or alignments provided for scrolling")
            return clips

        # Calculate layout parameters scaled to resolution
        scale = height / 360
        verse_spacing = int(60 * scale)
        top_margin = int(20 * scale)

        logger.info(f"Creating scrolling clips for {len(verses)} verses")

        # Create normal layer canvas (white, always visible)
        normal_canvas, verse_y_positions = render_verses_tall_canvas(
            verses=verses,
            width=width,
            font_path=str(self.font_path),
            font_size=self.font_size,
            text_color=self.normal_color,  # White
            verse_spacing=verse_spacing,
            top_margin=top_margin,
        )

        # Save normal canvas to temporary file
        normal_temp = tempfile.mktemp(suffix=".png", prefix="normal_canvas_")
        normal_canvas.save(normal_temp)
        logger.debug(f"Saved normal canvas: {normal_canvas.size}, path={normal_temp}")

        # Create scrolling position function
        def get_y_offset(t: float) -> int:
            """Calculate Y offset to keep current verse in upper third of screen.

            Args:
                t: Current time in seconds

            Returns:
                Y offset in pixels (negative to scroll down)
            """
            # Find which verse is currently active
            current_verse_idx = 0
            for i, pa in enumerate(pasuk_alignments):
                if pa.start_time <= t < pa.end_time:
                    current_verse_idx = i
                    break

            # If past all verses, show last verse
            if t >= pasuk_alignments[-1].end_time:
                current_verse_idx = len(pasuk_alignments) - 1

            # Calculate offset to position current verse in upper third
            verse_y = verse_y_positions[current_verse_idx]
            center_offset = height // 3  # Position at 1/3 from top
            y_offset = -(verse_y - center_offset)

            # Clamp to prevent showing blank space at top or bottom
            max_offset = 0  # Don't scroll above first verse
            min_offset = -(normal_canvas.height - height)  # Don't scroll below last verse
            clamped_offset = max(min_offset, min(max_offset, y_offset))

            return clamped_offset

        # Normal layer with scrolling
        normal_clip = (
            ImageClip(normal_temp)
            .with_duration(audio_duration)
            .with_position(lambda t: ('center', get_y_offset(t)))
        )
        clips.append(normal_clip)
        logger.debug("Created scrolling normal layer")

        # Create highlight layers (one per verse, also scrolling)
        for i, pa in enumerate(pasuk_alignments):
            # Capture start_time before lambda to avoid closure issues
            start_time = pa.start_time
            end_time = pa.end_time

            # Create highlight canvas (only this verse in gold)
            highlight_canvas = Image.new("RGBA", normal_canvas.size, (0, 0, 0, 0))

            # Extract verse number from reference
            verse_num = pa.reference.split(":")[-1] if ":" in pa.reference else str(i + 1)

            # Render verse image in gold
            verse_img = render_verse_image(
                verse_num=int(verse_num),
                hebrew_text=pa.hebrew_text,
                width=width,
                height=verse_spacing,
                font_path=str(self.font_path),
                font_size=self.font_size,
                text_color=self.highlight_color,  # Gold
                y_offset=0,
            )

            # Paste onto highlight canvas at same Y position as normal canvas
            highlight_canvas.paste(verse_img, (0, verse_y_positions[i]), verse_img)

            # Save highlight canvas
            highlight_temp = tempfile.mktemp(suffix=".png", prefix=f"highlight_{i}_")
            highlight_canvas.save(highlight_temp)

            # Create highlight clip (timed + scrolling)
            # FIX: Use absolute time by adding start_time offset
            # When .with_start() is used, moviepy calls the lambda with clip-relative time
            # So we add start_time to convert back to absolute video time
            highlight_clip = (
                ImageClip(highlight_temp)
                .with_duration(audio_duration)
                .with_position(lambda t, st=start_time: ('center', get_y_offset(t + st)))
                .with_start(start_time)
                .with_end(end_time)
            )
            clips.append(highlight_clip)

            logger.debug(
                f"Created scrolling highlight layer for verse {i+1}: {pa.reference}, "
                f"t={start_time:.2f}s to {end_time:.2f}s, "
                f"position_at_start={get_y_offset(start_time)}, "
                f"position_at_end={get_y_offset(end_time)}"
            )

        logger.info(
            f"Created {len(clips)} scrolling clips "
            f"(1 normal + {len(pasuk_alignments)} highlights)"
        )

        return clips

    def _image_to_clip(self, image: Image.Image, duration: float) -> ImageClip:
        """Convert PIL Image to ImageClip with temporary file.

        Args:
            image: PIL Image (RGB or RGBA)
            duration: Clip duration in seconds

        Returns:
            ImageClip with specified duration
        """
        temp_path = tempfile.mktemp(suffix=".png", prefix="torah_verse_")
        image.save(temp_path)
        clip = ImageClip(temp_path).with_duration(duration)
        logger.debug(f"Created ImageClip from {temp_path}")
        return clip
