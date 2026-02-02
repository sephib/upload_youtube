# Edited by Claude Code
"""VideoRenderer for creating synchronized videos with Hebrew text overlay."""

import tempfile
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
)

from src.lib.config import get_font_path, settings
from src.lib.exceptions import VideoRenderError
from src.lib.logging import get_logger
from src.models.timestamp_map import TimestampMap
from src.models.video import SynchronizedVideo
from src.services.text.hebrew_renderer import render_hebrew_text_image_simple

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
        timestamp_map: TimestampMap,
        output_path: Path,
        verses: list[tuple[str, str]] | None = None,
    ) -> SynchronizedVideo:
        """Render synchronized video with text overlay.

        Args:
            audio_file: Path to audio file
            timestamp_map: TimestampMap with verse timestamps
            output_path: Output video file path
            verses: Optional list of (reference, hebrew_text) tuples

        Returns:
            SynchronizedVideo model

        Raises:
            VideoRenderError: If rendering fails
        """
        logger.info(
            f"Starting video render",
            audio_file=str(audio_file),
            verse_count=len(timestamp_map.verse_timestamps),
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
            text_clips = self._create_text_clips(timestamp_map, verses, duration)

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

            # Create SynchronizedVideo model
            return SynchronizedVideo(
                file_path=output_path,
                format="mp4",
                resolution=self.resolution,
                frame_rate=self.fps,
                codec="h264",
                duration_seconds=duration,
                parasha_name=timestamp_map.parasha_name,
                aliyah_name=timestamp_map.aliyah_name,
            )

        except Exception as e:
            raise VideoRenderError(f"Video rendering failed: {e}") from e

    def _create_text_clips(
        self,
        timestamp_map: TimestampMap,
        verses: list[tuple[str, str]] | None = None,
        audio_duration: float = 10.0,
    ) -> list:
        """Create static text image with all verses displayed at once.

        No dynamic highlighting, no overlays - just a single static image
        with all verses visible for the entire video duration.

        Args:
            timestamp_map: TimestampMap with verse timestamps
            verses: Optional list of (reference, hebrew_text) tuples
            audio_duration: Audio duration in seconds (for clip duration)

        Returns:
            List containing single ImageClip with static text
        """
        width, height = self.resolution

        # Generate static image with all Hebrew verses
        text_image = render_hebrew_text_image_simple(
            verses=verses or [],
            width=width,
            height=height,
            font_path=str(self.font_path),
            font_size=self.font_size,
        )

        # Save to temporary file
        temp_image_path = tempfile.mktemp(suffix=".png", prefix="torah_verses_")
        text_image.save(temp_image_path)
        logger.debug(f"Saved static text image to {temp_image_path}")

        # Create single static ImageClip that displays for entire audio duration
        static_clip = ImageClip(temp_image_path).with_duration(audio_duration)

        logger.info(f"Created static image clip: {width}x{height}px, duration={audio_duration:.1f}s")

        return [static_clip]
