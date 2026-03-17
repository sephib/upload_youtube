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

    Creates an individual verse image for use in multi-layer video composition.
    This function enables verse-level highlighting by allowing separate rendering
    of normal (white) and highlighted (gold) text layers.

    Args:
        verse_num: Verse number for display (e.g., 1, 2, 3)
        hebrew_text: Hebrew text with Nikkud and T'amim
        width: Image width in pixels
        height: Image height in pixels
        font_path: Path to TrueType/OpenType font file
        font_size: Font size in points
        text_color: Hex color for text (e.g., "#FFFFFF" or "#FFD700")
        y_offset: Vertical offset for positioning this verse (pixels from top)

    Returns:
        PIL Image with RGBA mode (transparent background, colored text)

    Example:
        >>> # Create normal layer (white)
        >>> normal_img = render_verse_image(
        ...     1, "הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם", 1280, 720,
        ...     "/System/Library/Fonts/ArialHB.ttc", 40, "#FFFFFF", 20
        ... )
        >>> # Create highlight layer (gold)
        >>> highlight_img = render_verse_image(
        ...     1, "הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם", 1280, 720,
        ...     "/System/Library/Fonts/ArialHB.ttc", 40, "#FFD700", 20
        ... )
    """
    logger.debug(f"{verse_num=}, {width=}, {height=}, {text_color=}, {y_offset=}")

    # Create transparent image (RGBA mode for transparency support)
    image = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    # Format verse with number: (1) hebrew_text
    display_text = f"({verse_num}) {hebrew_text}"

    # Calculate text wrapping area
    scale = height / 360
    right_margin = int(20 * scale)
    left_margin = int(20 * scale)
    text_width = width - left_margin - right_margin

    # Wrap text to fit within image width
    lines = _wrap_text(draw, display_text, font, text_width)
    # Apply RTL reordering per line for Hebrew display
    lines = [get_display(line) for line in lines]
    wrapped_text = "\n".join(lines)

    # Draw text at specified y_offset with right alignment
    line_spacing = font_size + 5
    draw.multiline_text(
        (width - right_margin, y_offset),
        wrapped_text,
        font=font,
        fill=text_color,
        anchor="ra",
        spacing=line_spacing,
        align="right",
    )

    logger.debug(f"Rendered verse {verse_num}: {len(lines)} lines, color={text_color}")
    return image


def render_verses_tall_canvas(
    verses: list[tuple[str, str]],
    width: int,
    font_path: str,
    font_size: int,
    text_color: str = "#FFFFFF",
    verse_spacing: int = 60,
    top_margin: int = 20,
) -> tuple[Image.Image, list[int]]:
    """Render all verses on a tall canvas for scrolling video.

    Creates a single tall canvas with all verses laid out vertically,
    enabling smooth scrolling through the verses during video playback.

    Args:
        verses: List of (reference, hebrew_text) tuples
        width: Canvas width in pixels
        font_path: Path to TrueType/OpenType font file
        font_size: Font size in points
        text_color: Hex color for text (e.g., "#FFFFFF" or "#FFD700")
        verse_spacing: Vertical spacing between verses in pixels
        top_margin: Top margin in pixels

    Returns:
        tuple: (tall_canvas_image, verse_y_positions)
            - tall_canvas_image: PIL Image with RGBA mode containing all verses
            - verse_y_positions: List of Y coordinates for each verse's top position

    Example:
        >>> verses = [("Deuteronomy 32:1", "הַאֲזִ֥ינוּ..."), ...]
        >>> canvas, positions = render_verses_tall_canvas(
        ...     verses, 1280, "/System/Library/Fonts/ArialHB.ttc", 40
        ... )
        >>> print(f"Canvas size: {canvas.size}, Verse 1 at Y={positions[0]}")
    """
    logger.debug(
        f"Creating tall canvas: {len(verses)} verses, "
        f"{width=}px, {font_size=}pt, spacing={verse_spacing}px"
    )

    # Calculate total height needed for all verses
    total_height = top_margin + (len(verses) * verse_spacing)

    # Create tall RGBA canvas (transparent background)
    canvas = Image.new("RGBA", (width, total_height), color=(0, 0, 0, 0))

    # Track Y position for each verse
    verse_y_positions = []

    # Render each verse onto canvas at its designated position
    for i, (ref, hebrew_text) in enumerate(verses):
        # Extract verse number from reference
        verse_num = ref.split(":")[-1] if ":" in ref else str(i + 1)

        # Calculate Y position for this verse
        y_pos = top_margin + (i * verse_spacing)
        verse_y_positions.append(y_pos)

        # Render verse image
        verse_img = render_verse_image(
            verse_num=int(verse_num),
            hebrew_text=hebrew_text,
            width=width,
            height=verse_spacing,  # Each verse gets its own height slice
            font_path=font_path,
            font_size=font_size,
            text_color=text_color,
            y_offset=0,  # Draw at top of the verse slice
        )

        # Paste verse image onto tall canvas at calculated Y position
        canvas.paste(verse_img, (0, y_pos), verse_img)

        logger.debug(f"Placed verse {i+1} ({ref}) at Y={y_pos}px")

    logger.info(
        f"Created tall canvas: {width}x{total_height}px with {len(verses)} verses"
    )
    return canvas, verse_y_positions
