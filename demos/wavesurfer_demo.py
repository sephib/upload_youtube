"""Interactive Audio Waveform Visualization with WaveSurfer.js + marimo

Edited by Claude Code

This marimo notebook demonstrates the WavesurferWidget for interactive audio
waveform visualization with region annotation. Features include:

- Audio waveform visualization with zoom controls
- Draggable/resizable regions with confidence-based coloring
- Two-way sync between table and waveform
- Play/pause controls with periodic time sync
- Isolated segment playback via play_range
- Timeline with time markers

Launch: marimo run demos/wavesurfer_demo.py
"""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def imports():
    import marimo as mo

    return (mo,)


@app.cell
def title(mo):
    mo.md("""
    # Interactive Audio Waveform Visualization

    Custom `anywidget` integrating **wavesurfer.js** with marimo for interactive
    audio waveform visualization and segment annotation.

    **Features**: Zoom controls, confidence-based region coloring,
    isolated segment playback, bidirectional table sync.

    ---
    """)
    return


@app.cell
def widget_setup(mo):
    """Import the WavesurferWidget."""
    import sys
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    if str(repo_root / "src") not in sys.path:
        sys.path.insert(0, str(repo_root / "src"))

    from widgets.wavesurfer_widget import WavesurferWidget

    mo.md("Widget imported successfully.")
    return WavesurferWidget, repo_root


@app.cell
def audio_file_picker(mo):
    """File picker for audio upload."""
    mo.md("""
    ## Step 1: Load Audio

    Upload an audio file or let the demo find a sample from the project.

    Supported formats: MP3, WAV, OGG, M4A
    """)
    file_picker = mo.ui.file(
        filetypes=[".mp3", ".wav", ".ogg", ".m4a"],
        label="Upload Audio File",
    )
    file_picker
    return (file_picker,)


@app.cell
def load_audio(file_picker, mo, repo_root):
    """Load audio from uploaded file or fallback to sample."""
    audio_bytes = None
    audio_name = "No audio loaded"
    status_message = ""

    if file_picker.value is not None and len(file_picker.value) > 0:
        audio_bytes = file_picker.value[0].contents
        audio_name = file_picker.value[0].name
        status_message = f"**Loaded:** {audio_name}"
    else:
        sample_dirs = [
            repo_root / "demos" / "assets",
            repo_root / "data" / "audio",
            repo_root / "data" / "cache" / "audio_segments",
        ]

        for sample_dir in sample_dirs:
            if not sample_dir.exists():
                continue
            if sample_dir.is_file():
                with open(sample_dir, "rb") as f:
                    audio_bytes = f.read()
                audio_name = sample_dir.name
                break
            audio_files = list(sample_dir.glob("*.mp3")) + list(sample_dir.glob("*.wav"))
            if audio_files:
                sample_file = audio_files[0]
                with open(sample_file, "rb") as f:
                    audio_bytes = f.read()
                audio_name = sample_file.name
                break

        if audio_bytes:
            status_message = f"**Using sample:** {audio_name}"
        else:
            status_message = "**No audio file found.** Upload one above."

    mo.md(status_message)
    return (audio_bytes,)


@app.cell
def create_sample_regions():
    """Create sample regions with confidence values for demo."""
    # Edited by Claude Code
    sample_regions = [
        {
            "id": "intro",
            "start": 0.0,
            "end": 3.0,
            "label": "Introduction",
            "confidence": 0.92,
            "drag": True,
            "resize": True,
        },
        {
            "id": "segment_1",
            "start": 3.0,
            "end": 8.5,
            "label": "Segment 1",
            "confidence": 0.78,  # low confidence -> orange
            "drag": True,
            "resize": True,
        },
        {
            "id": "segment_2",
            "start": 8.5,
            "end": 15.0,
            "label": "Segment 2",
            "confidence": 0.95,
            "corrected": True,  # manually corrected -> green
            "drag": True,
            "resize": True,
        },
        {
            "id": "outro",
            "start": 15.0,
            "end": 20.0,
            "label": "Conclusion",
            "confidence": 0.88,
            "drag": True,
            "resize": True,
        },
    ]
    return (sample_regions,)


@app.cell
def create_widget(WavesurferWidget, audio_bytes, mo, sample_regions):
    """Create the wavesurfer widget if audio is loaded."""
    if audio_bytes is None:
        mo.stop(True, mo.md("Waiting for audio file..."))

    widget = WavesurferWidget(
        audio_data=audio_bytes,
        regions=sample_regions,
        waveform_color="#4F4A85",
        progress_color="#7C3AED",
        height=150,
        zoom_level=50,
    )

    widget_ui = mo.ui.anywidget(widget)

    mo.md("""
    ## Step 2: Interactive Waveform

    - **Zoom**: Use Zoom +/- buttons or set via slider below
    - **Regions**: Drag edges to resize, drag body to move
    - **Colors**: Blue = normal, Orange = low confidence, Green = corrected, Gold = selected
    """)
    return widget, widget_ui


@app.cell
def display_widget(widget_ui):
    """Display the wavesurfer widget."""
    widget_ui
    return


@app.cell
def zoom_control(mo, widget):
    """Zoom slider for fine-grained control."""
    zoom_slider = mo.ui.slider(
        start=10, stop=500, step=10,
        value=widget.zoom_level,
        label="Zoom (px/sec)",
    )
    zoom_slider
    return (zoom_slider,)


@app.cell
def apply_zoom(zoom_slider, widget):
    """Apply zoom slider value to widget."""
    widget.zoom_level = zoom_slider.value
    return


@app.cell
def regions_table(mo, widget_ui):
    """Display regions as a table with two-way sync."""
    mo.md("## Step 3: Regions Table (Two-Way Sync)")

    if not hasattr(widget_ui, "value"):
        mo.stop(True)

    regions = widget_ui.value.get("regions", [])

    table_data = [
        {
            "ID": r["id"],
            "Label": r.get("label", ""),
            "Start (s)": round(r["start"], 3),
            "End (s)": round(r["end"], 3),
            "Duration (s)": round(r["end"] - r["start"], 3),
            "Confidence": r.get("confidence", ""),
            "Corrected": "Yes" if r.get("corrected") else "",
        }
        for r in regions
    ]

    table = mo.ui.table(
        table_data,
        selection="single",
        label="Audio Regions",
    )

    table
    return (table,)


@app.cell
def sync_table_to_waveform(mo, table, widget):
    """When user clicks a table row, seek to that region and play it."""
    if not table.value:
        mo.stop(True)

    selected_row = table.value[0]
    region_id = selected_row["ID"]

    for region in widget.regions:
        if region["id"] == region_id:
            widget.selected_region_id = region_id
            widget.play_range = [region["start"], region["end"]]
            break

    mo.md(f"**Playing:** {selected_row['Label']} ({region_id})")
    return


@app.cell
def widget_state_display(mo, widget_ui):
    """Display current widget state."""
    if not hasattr(widget_ui, "value"):
        mo.stop(True)

    state = widget_ui.value
    current_time = state.get("current_time", 0.0)
    duration = state.get("duration", 0.0)
    is_playing = state.get("is_playing", False)
    selected_id = state.get("selected_region_id", "")
    zoom = state.get("zoom_level", 50)

    mo.md(
        f"""
        ### Widget State

        | Property | Value |
        |----------|-------|
        | Playback | {'Playing' if is_playing else 'Paused'} |
        | Time | {current_time:.3f}s / {duration:.3f}s |
        | Selected | {selected_id or '(none)'} |
        | Zoom | {zoom} px/sec |
        | Regions | {len(state.get('regions', []))} |
        | Speed | {state.get('playback_speed', 1.0):.2f}x |
        """
    )
    return


@app.cell
def export_section(mo, widget_ui):
    """Export regions as JSON."""
    mo.md("## Step 4: Export Annotations")

    if not hasattr(widget_ui, "value"):
        mo.stop(True)

    export_btn = mo.ui.run_button(label="Export Regions as JSON")
    export_btn
    return (export_btn,)


@app.cell
def export_handler(mo, widget_ui, export_btn):
    """Handle export button click."""
    import json

    if not export_btn.value:
        mo.stop(True)

    _regions = widget_ui.value.get("regions", [])
    json_output = json.dumps(_regions, indent=2)

    mo.vstack(
        [
            mo.callout("Regions exported! Copy the JSON below:", kind="success"),
            mo.ui.code_editor(value=json_output, language="json", disabled=True),
        ]
    )
    return


@app.cell
def color_legend(mo):
    mo.md("""
    ---

    ## Region Color Legend

    | Color | Meaning | Condition |
    |-------|---------|-----------|
    | Cornflower Blue | Normal alignment | confidence >= 0.85 |
    | Orange | Low confidence | confidence < 0.85 |
    | Gold | Currently selected | user clicked region |
    | Green | Manually corrected | corrected = True |

    ## Architecture

    ```
    Python: WavesurferWidget (anywidget + traitlets)
      audio_data, regions, current_time, is_playing,
      selected_region_id, zoom_level, play_range, duration
                    | traitlets sync
    JavaScript: wavesurfer.js v7 (ESM from CDN)
      Regions plugin (drag/resize/click)
      Timeline plugin (time axis)
      Zoom via minPxPerSec
      play_range -> play(start) + stop at end
    ```

    ---

    **Created by**: Torah Sync Project | **Edited by Claude Code**
    """)
    return


if __name__ == "__main__":
    app.run()
