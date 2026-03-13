# Edited by Claude Opus 4.6
"""Hebrew text rendering using PIL for static image generation.

Renders Hebrew text with vowel points (nikkud) and cantillation marks (te'amim)
using PIL's built-in text rendering with python-bidi for RTL text direction.

Note: PIL has limitations with complex Unicode combining characters - some
advanced diacritics may render as box characters. This is a known limitation
of PIL/Pillow's text rendering engine and cannot be resolved without switching
to a different rendering stack (e.g., Cairo, Pango).
"""

from pathlib import Path

from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

from src.lib.logging import get_logger

logger = get_logger(__name__)


def render_hebrew_text_image_simple(
    verses: list[tuple[str, str]],
    width: int,
    height: int,
    font_path: str,
    font_size: int,
) -> Image.Image:
    """Render Hebrew verses with diacritics to a static image.

    Creates a single static image with all verses displayed at once on a black background.
    Handles right-to-left text direction, verse numbering, and automatic text wrapping.

    Features:
    - RTL text rendering using python-bidi for proper Hebrew text direction
    - Verse numbers in parentheses: (1) verse text, (2) verse text, etc.
    - Manual word wrapping to prevent text cutoff at image boundaries
    - Right-aligned multiline text layout
    - Support for Hebrew vowel points (nikkud) and cantillation marks (te'amim)

    Known Limitations:
    - Some complex Unicode combining characters may render as box characters (□)
      due to PIL/Pillow's text rendering limitations. This is a known issue that
      cannot be resolved without switching to Cairo/Pango rendering.

    Args:
        verses: List of (reference, hebrew_text) tuples.
                Reference format: "Book Chapter:Verse" or "Section - Intro"
                Example: [("Deuteronomy 32:1", "הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם וַאֲדַבֵּ֑רָה")]
        width: Image width in pixels
        height: Image height in pixels
        font_path: Path to TrueType/OpenType font file (recommended: Arial Hebrew)
        font_size: Font size in points

    Returns:
        PIL Image object with rendered Hebrew text on black background

    Example:
        >>> verses = [
        ...     ("Deuteronomy 32:1", "הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם וַאֲדַבֵּ֑רָה"),
        ...     ("Deuteronomy 32:2", "יַעֲרֹ֤ף כַּמָּטָר֙ לִקְחִ֔י")
        ... ]
        >>> image = render_hebrew_text_image_simple(
        ...     verses, 640, 360, "/System/Library/Fonts/ArialHB.ttc", 20
        ... )
        >>> image.save("output.png")
    """
    logger.debug(f"Rendering {len(verses)} verses to static image: {width}x{height}px, {font_size}pt")

    # Scale margins/padding proportionally to resolution. Edited by Claude Code
    scale = height / 360
    top_margin = int(20 * scale)
    left_margin = int(20 * scale)
    right_margin = int(20 * scale)
    bottom_margin = int(20 * scale)
    text_width = width - left_margin - right_margin
    available_height = height - top_margin - bottom_margin
    min_font_size = max(8, int(8 * scale))
    verse_padding = int(10 * scale)

    # Auto-scale: find the largest font size that fits all text
    current_font_size = font_size
    while current_font_size >= min_font_size:
        total_height = _measure_total_height(
            verses, text_width, width, right_margin, font_path, current_font_size, verse_padding,
        )
        if total_height <= available_height:
            break
        current_font_size -= 1

    if current_font_size < font_size:
        logger.info(f"Auto-scaled font: {font_size}pt -> {current_font_size}pt to fit {len(verses)} verses")

    # Create black background image
    image = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, current_font_size)
    line_spacing = current_font_size + 5
    y_offset = top_margin

    for i, (ref, hebrew_text) in enumerate(verses):
        display_text = _format_verse(ref, hebrew_text, i)
        # Wrap in logical order first, then apply bidi per line
        # so that line 1 = beginning of verse, line 2 = continuation
        lines = _wrap_text(draw, display_text, font, text_width)
        lines = [get_display(line) for line in lines]
        wrapped_text = "\n".join(lines)

        draw.multiline_text(
            (width - right_margin, y_offset),
            wrapped_text,
            font=font,
            fill="white",
            anchor="ra",
            spacing=line_spacing,
            align="right",
        )

        bbox = draw.multiline_textbbox(
            (width - right_margin, y_offset),
            wrapped_text,
            font=font,
            anchor="ra",
            spacing=line_spacing,
            align="right",
        )
        text_height = bbox[3] - bbox[1]

        logger.debug(f"Rendered verse {i+1}/{len(verses)}: {ref}, lines={len(lines)}, height={text_height}px")
        y_offset += text_height + verse_padding

    logger.info(f"Static image rendered successfully with {len(verses)} verses")
    return image


def _format_verse(ref: str, hebrew_text: str, index: int) -> str:
    """Format a verse with its number for display."""
    if "Intro" in ref:
        return hebrew_text
    verse_num = ref.split(":")[-1] if ":" in ref else str(index)
    return f"({verse_num}) {hebrew_text}"


def _wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> list[str]:
    """Wrap text into lines that fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line: list[str] = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        elif current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            lines.append(word)
            current_line = []

    if current_line:
        lines.append(" ".join(current_line))
    return lines


def _measure_total_height(
    verses: list[tuple[str, str]],
    text_width: int,
    image_width: int,
    right_margin: int,
    font_path: str,
    font_size: int,
    verse_padding: int,
) -> int:
    """Dry-run measurement of total text height at given font size."""
    # Use a temporary image for measurement only
    tmp_img = Image.new("RGB", (image_width, 1))
    draw = ImageDraw.Draw(tmp_img)
    font = ImageFont.truetype(font_path, font_size)
    line_spacing = font_size + 5
    total = 0

    for i, (ref, hebrew_text) in enumerate(verses):
        display_text = _format_verse(ref, hebrew_text, i)
        lines = _wrap_text(draw, display_text, font, text_width)
        lines = [get_display(line) for line in lines]
        wrapped_text = "\n".join(lines)

        bbox = draw.multiline_textbbox(
            (image_width - right_margin, 0),
            wrapped_text,
            font=font,
            anchor="ra",
            spacing=line_spacing,
            align="right",
        )
        total += (bbox[3] - bbox[1]) + verse_padding

    return total
