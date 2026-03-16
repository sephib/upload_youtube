# Edited by Claude Opus 4.6 (fixed: each cell self-displays as last expression)
"""Marimo app for manual alignment correction.

Displays psukim (verses) as text with start/end times,
allowing the user to adjust timestamps per pasuk.
Backend: DuckDB via repositories.

Launch: torah-sync correct
   or: marimo run src/apps/alignment_editor.py
"""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def verse_table(mo):
    mo.md("""
    # Alignment Editor
    """)
    return


@app.cell(hide_code=True)
def db_setup(mo):
    """Initialize DuckDB connection and load playlists."""
    from src.repositories.alignment_repo import AlignmentRunRepository
    from src.repositories.alya_audio_repo import AlyaAudioRepository
    from src.repositories.alya_repo import AlyaRepository
    from src.repositories.db import get_connection
    from src.repositories.pasuk_alignment_repo import PasukAlignmentRepository
    from src.repositories.playlist_repo import PlaylistRepository

    get_connection()

    alya_repo = AlyaRepository()
    audio_repo = AlyaAudioRepository()
    run_repo = AlignmentRunRepository()
    pa_repo = PasukAlignmentRepository()

    playlists = PlaylistRepository().list_all()
    playlist_options = {p.name: p.id for p in playlists}

    playlist_dropdown = mo.ui.dropdown(
        options=playlist_options,
        label="Select Parasha",
    )
    playlist_dropdown
    return alya_repo, audio_repo, pa_repo, playlist_dropdown, run_repo


@app.cell(hide_code=True)
def alya_selector(alya_repo, mo, playlist_dropdown):
    """Select an alya within the chosen playlist."""
    mo.stop(playlist_dropdown.value is None, mo.md("Select a Parasha above."))

    alyot = alya_repo.list_by_playlist(playlist_dropdown.value)
    alya_options = {f"{a.name} (id={a.id}, {a.state.value})": a.id for a in alyot}

    alya_dropdown = mo.ui.dropdown(
        options=alya_options,
        label="Select Alya",
    )
    alya_dropdown
    return (alya_dropdown,)


@app.cell(hide_code=True)
def load_alignment(alya_dropdown, audio_repo, mo, pa_repo, run_repo):
    """Load the latest alignment run and its pasuk alignments."""
    mo.stop(alya_dropdown.value is None, mo.md("Select an Alya above."))

    alya_id = alya_dropdown.value
    audio = audio_repo.get_by_alya(alya_id)
    mo.stop(audio is None, mo.md("**No audio found for this alya.**"))

    alignment_run = run_repo.get_latest_by_audio(audio.id)
    mo.stop(
        alignment_run is None,
        mo.md("**No alignment run found. Run `torah-sync align` first.**"),
    )

    pasuk_alignments = pa_repo.list_by_alignment_run(alignment_run.id)
    mo.stop(len(pasuk_alignments) == 0, mo.md("**No verse alignments found.**"))
    return alignment_run, audio, pasuk_alignments


@app.cell(hide_code=True)
def audio_waveform(audio, mo, pasuk_alignments):
    # Edited by Claude Code
    """Waveform player with verse regions using WavesurferWidget."""
    from pathlib import Path

    from src.widgets.wavesurfer_widget import WavesurferWidget

    audio_path = Path(audio.file_path).resolve()
    mo.stop(not audio_path.exists(), mo.md(f"*Audio file not found: {audio.file_path}*"))

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    regions = [
        {
            "id": str(pa.id),
            "start": pa.start_time,
            "end": pa.end_time,
            "label": pa.reference,
            "confidence": pa.confidence,
            "corrected": pa.manually_corrected,
            "drag": True,
            "resize": True,
        }
        for pa in pasuk_alignments
    ]

    waveform = WavesurferWidget(
        audio_data=audio_bytes,
        regions=regions,
        height=150,
        zoom_level=50,
    )

    waveform_ui = mo.ui.anywidget(waveform)
    waveform_ui
    return (waveform,)


@app.cell(hide_code=True)
def layout(mo, pasuk_alignments):
    """Display the verse table with alignment data."""
    table_data = [
        {
            "order": pa.verse_order,
            "reference": pa.reference,
            "hebrew_text": (
                pa.hebrew_text[:60] + ("..." if len(pa.hebrew_text) > 60 else "")
            ),
            "start_time": round(pa.start_time, 3),
            "end_time": round(pa.end_time, 3),
            "duration": round(pa.end_time - pa.start_time, 3),
            "confidence": round(pa.confidence, 2),
            "corrected": "yes" if pa.manually_corrected else "",
        }
        for pa in pasuk_alignments
    ]

    table = mo.ui.table(
        table_data,
        selection="single",
        label="Verse Alignments",
    )
    table
    return (table,)


@app.cell(hide_code=True)
def trim_panel(audio, mo, pasuk_alignments):
    # Edited by Claude Opus 4.6 (trim intro offset feature)
    """Set a trim-start offset to skip intro audio (e.g. section description)."""
    first_pa = pasuk_alignments[0]
    trim_input = mo.ui.number(
        value=first_pa.start_time,
        start=0.0,
        stop=audio.duration_seconds,
        step=0.1,
        label="Trim start (s) — skip intro audio before first verse",
    )
    trim_btn = mo.ui.run_button(label="Apply Trim")
    mo.vstack([
        mo.md("### Trim Intro"),
        mo.md(
            f"Current first verse starts at **{first_pa.start_time:.2f}s**. "
            "Set the trim point to shift all verses forward."
        ),
        mo.hstack([trim_input, trim_btn]),
    ])
    return trim_btn, trim_input


@app.cell(hide_code=True)
def apply_trim(
    alignment_run,
    mo,
    pa_repo,
    pasuk_alignments,
    run_repo,
    trim_btn,
    trim_input,
):
    # Edited by Claude Opus 4.6
    """Apply trim offset: shift all verse timestamps so first verse starts at trim point."""
    mo.stop(not trim_btn.value)

    offset = trim_input.value
    first_start = pasuk_alignments[0].start_time

    if abs(offset - first_start) < 0.001:
        mo.stop(True, mo.callout("No change — trim value matches current start.", kind="warn"))

    shift = offset - first_start
    for _pa in pasuk_alignments:
        if _pa.original_start_time is None:
            _pa.original_start_time = _pa.start_time
            _pa.original_end_time = _pa.end_time
        _pa.start_time = max(0.0, _pa.start_time + shift)
        _pa.end_time = max(0.0, _pa.end_time + shift)
        _pa.manually_corrected = True
        pa_repo.update(_pa)

    if not alignment_run.manually_corrected:
        from datetime import datetime as _datetime
        alignment_run.original_quality = alignment_run.alignment_quality
        alignment_run.manually_corrected = True
        alignment_run.corrected_at = _datetime.now()
        run_repo.mark_corrected(alignment_run)

    mo.callout(
        f"**Trimmed:** shifted all {len(pasuk_alignments)} verses by {shift:+.3f}s "
        f"(first verse now starts at {offset:.2f}s)",
        kind="success",
    )
    return


@app.cell(hide_code=True)
def table_to_waveform(mo, pasuk_alignments, table, waveform):
    # Edited by Claude Code
    """Sync table selection to waveform: seek and play the selected verse segment."""
    mo.stop(len(table.value) == 0)

    _selected_row = table.value[0]
    _selected_order = _selected_row["order"]
    _pa = next(p for p in pasuk_alignments if p.verse_order == _selected_order)

    waveform.selected_region_id = str(_pa.id)
    waveform.play_range = [_pa.start_time, _pa.end_time]
    return


@app.cell(hide_code=True)
def edit_panel(audio, mo, pasuk_alignments, table):
    """Edit start/end times for the selected verse."""
    mo.stop(
        len(table.value) == 0,
        mo.md("*Click a row above to edit its timestamps.*"),
    )

    selected_row = table.value[0]
    selected_order = selected_row["order"]

    pa = next(p for p in pasuk_alignments if p.verse_order == selected_order)

    start_input = mo.ui.number(
        value=pa.start_time,
        start=0.0,
        stop=audio.duration_seconds,
        step=0.05,
        label="Start time (s)",
    )
    end_input = mo.ui.number(
        value=pa.end_time,
        start=0.0,
        stop=audio.duration_seconds,
        step=0.05,
        label="End time (s)",
    )

    mo.vstack([
        mo.md(f"### Editing: {pa.reference}"),
        mo.hstack([start_input, end_input]),
    ])
    return end_input, pa, start_input


@app.cell
def save_button(mo):
    """Button to apply edits."""
    save_btn = mo.ui.run_button(label="Apply Edit")
    save_btn
    return (save_btn,)


@app.cell
def apply_edit(
    alignment_run,
    end_input,
    mo,
    pa,
    pa_repo,
    run_repo,
    save_btn,
    start_input,
):
    """Apply the timestamp edit to DuckDB when save is clicked."""
    mo.stop(not save_btn.value)

    new_start = start_input.value
    new_end = end_input.value

    if new_end <= new_start:
        mo.stop(
            True,
            mo.callout(
                f"**Invalid:** end_time ({new_end}) must be > start_time ({new_start})",
                kind="danger",
            ),
        )

    # Save original values on first correction
    if pa.original_start_time is None:
        pa.original_start_time = pa.start_time
        pa.original_end_time = pa.end_time

    pa.start_time = new_start
    pa.end_time = new_end
    pa.manually_corrected = True
    pa_repo.update(pa)

    # Mark alignment run as corrected
    if not alignment_run.manually_corrected:
        from datetime import datetime

        alignment_run.original_quality = alignment_run.alignment_quality
        alignment_run.manually_corrected = True
        alignment_run.corrected_at = datetime.now()
        run_repo.mark_corrected(alignment_run)

    mo.callout(
        f"**Saved** {pa.reference}: {new_start:.3f}s - {new_end:.3f}s",
        kind="success",
    )
    return


if __name__ == "__main__":
    app.run()
