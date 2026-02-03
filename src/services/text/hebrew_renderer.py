# Edited by Claude Code
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

    # Create black background image
    image = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(image)

    # Load font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate layout
    left_margin = 20
    right_margin = 20
    text_width = width - left_margin - right_margin
    y_offset = 20  # Top margin
    line_spacing = font_size + 5  # Line spacing within multiline text

    for i, (ref, hebrew_text) in enumerate(verses):
        # Format verse with number at the BEGINNING
        if "Intro" in ref:
            # Intro has no verse number
            display_text = hebrew_text
        else:
            # Extract verse number (e.g., "Deuteronomy 32:3" -> "3")
            verse_num = ref.split(":")[-1] if ":" in ref else str(i)
            # Put verse number BEFORE the text
            # Use parentheses which are more stable with RTL than period
            # Format: ({num}) {text}
            display_text = f"({verse_num}) {hebrew_text}"

        # Apply RTL bidirectional text reordering
        # Converts logical order (storage) to visual order (display)
        display_text = get_display(display_text)

        # Manual text wrapping - PIL doesn't auto-wrap, so we split into lines
        words = display_text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            # Measure width of test line
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= text_width:
                current_line.append(word)
            else:
                # Line is too long, save current line and start new one
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)
                    current_line = []

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        # Join lines with newlines for multiline_text
        wrapped_text = "\n".join(lines)

        # Draw the wrapped text
        draw.multiline_text(
            (width - right_margin, y_offset),  # Right side
            wrapped_text,
            font=font,
            fill="white",
            anchor="ra",  # Right-aligned, top of text
            spacing=line_spacing,
            align="right",
        )

        # Calculate how many lines this verse took
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

        # Move down for next verse (add some padding between verses)
        y_offset += text_height + 10

    logger.info(f"Static image rendered successfully with {len(verses)} verses")
    return image
