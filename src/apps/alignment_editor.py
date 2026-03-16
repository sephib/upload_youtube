# Edited by Claude Code
"""Marimo app for manual alignment correction.

Displays psukim (verses) as text with start/end times,
allowing the user to adjust timestamps by dragging waveform regions.
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

    Drag region edges on the waveform to adjust verse boundaries,
    then click **Save All** to persist changes.
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
    return waveform, waveform_ui


@app.cell(hide_code=True)
def layout(mo, pasuk_alignments, waveform_ui):
    # Edited by Claude Code
    """Display verse table reflecting waveform region edits."""
    _wf_regions = waveform_ui.value.get("regions", []) if waveform_ui.value else []
    _region_map = {r["id"]: r for r in _wf_regions}

    table_data = []
    for _pa in pasuk_alignments:
        _region = _region_map.get(str(_pa.id))
        _start = _region["start"] if _region else _pa.start_time
        _end = _region["end"] if _region else _pa.end_time
        _changed = _region and (
            abs(_start - _pa.start_time) > 0.001 or abs(_end - _pa.end_time) > 0.001
        )
        table_data.append({
            "order": _pa.verse_order,
            "reference": _pa.reference,
            "hebrew_text": (
                _pa.hebrew_text[:60] + ("..." if len(_pa.hebrew_text) > 60 else "")
            ),
            "start_time": round(_start, 3),
            "end_time": round(_end, 3),
            "duration": round(_end - _start, 3),
            "confidence": round(_pa.confidence, 2),
            "edited": "*" if _changed else "",
        })

    table = mo.ui.table(
        table_data,
        selection="single",
        label="Verse Alignments",
    )
    table
    return (table,)


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
def edit_panel(mo):
    # Edited by Claude Code
    """Save All button — always renders, no mo.stop."""
    save_all_btn = mo.ui.run_button(label="Save All Alignments")

    mo.vstack([
        mo.md("### Save Changes"),
        mo.md(
            "Drag region edges on the waveform above to adjust verse boundaries. "
            "Edited verses show **\\*** in the table. Click below to save all changes."
        ),
        save_all_btn,
    ])
    return (save_all_btn,)


@app.cell(hide_code=True)
def _(
    alignment_run,
    mo,
    pa_repo,
    pasuk_alignments,
    run_repo,
    save_all_btn,
    waveform_ui,
):
    # Edited by Claude Code
    """Persist all waveform region edits to DuckDB when save_all_btn is clicked."""
    mo.stop(not save_all_btn.value)

    _wf_regions = waveform_ui.value.get("regions", []) if waveform_ui.value else []
    _region_map = {r["id"]: r for r in _wf_regions}

    _updated_count = 0
    for _pa in pasuk_alignments:
        _region = _region_map.get(str(_pa.id))
        if not _region:
            continue

        _new_start = _region["start"]
        _new_end = _region["end"]

        if (
            abs(_new_start - _pa.start_time) < 0.001
            and abs(_new_end - _pa.end_time) < 0.001
        ):
            continue

        if _pa.original_start_time is None:
            _pa.original_start_time = _pa.start_time
            _pa.original_end_time = _pa.end_time

        _pa.start_time = _new_start
        _pa.end_time = _new_end
        _pa.manually_corrected = True
        pa_repo.update(_pa)
        _updated_count += 1

    if _updated_count > 0 and not alignment_run.manually_corrected:
        from datetime import datetime as _datetime

        alignment_run.original_quality = alignment_run.alignment_quality
        alignment_run.manually_corrected = True
        alignment_run.corrected_at = _datetime.now()
        run_repo.mark_corrected(alignment_run)

    if _updated_count > 0:
        _msg = mo.callout(
            f"**Saved {_updated_count}** of {len(pasuk_alignments)} "
            "verse alignments to DuckDB.",
            kind="success",
        )
    else:
        _msg = mo.callout(
            "No changes detected — all regions match stored values.", kind="warn",
        )

    _msg
    return


if __name__ == "__main__":
    app.run()
