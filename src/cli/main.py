# Edited by Claude Opus 4.6 (rewritten for 3-phase pipeline)
"""CLI entry point for Torah Sync application."""

import sys
from pathlib import Path

import click

from src.lib.config import settings
from src.lib.exceptions import TorahSyncError
from src.lib.filename_parser import validate_audio_file
from src.lib.logging import get_logger, setup_logging

from src.lib.config import get_log_dir

setup_logging(
    log_level=settings.get("log_level", "INFO"),
    log_file=get_log_dir() / "torah-sync.log",
    use_json=False,
)

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="torah-sync")
def cli():
    """Torah Sync - Automated Torah Reading Audio-Visual Synchronization.

    Three-phase pipeline:
      1. align  - sync audio + text -> DuckDB
      2. correct - review/fix alignment in marimo app
      3. render  - generate video from finalized alignment
    """
    pass


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
def align(audio_file: Path):
    """Align audio with Hebrew text and save to DuckDB.

    AUDIO_FILE should follow the naming convention:
    פרשת {Parasha} - {Aliyah} - נוסח אשכנז.{ext}

    Example:
        torah-sync align "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"
    """
    logger.info(f"Aligning audio file {audio_file.name}")

    try:
        validate_audio_file(audio_file)

        from src.services.alignment_pipeline import AlignmentPipeline

        pipeline = AlignmentPipeline()
        alignment_run, pasuk_alignments = pipeline.align(audio_file)

        click.echo(f"✓ Alignment complete (run_id={alignment_run.id})")
        click.echo(f"  Verses: {len(pasuk_alignments)}")
        click.echo(f"  Quality: {alignment_run.alignment_quality:.2f}")

    except TorahSyncError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(2)


# Edited by Claude Opus 4.6 — align by alya_id for megillot
@cli.command("align-alya")
@click.argument("alya_id", type=int)
def align_alya(alya_id: int):
    """Align a pre-ingested alya by its DB id.

    Use this for megillot or any audio already registered in DuckDB
    (bypasses filename parsing).

    Example:
        torah-sync align-alya 487
        torah-sync status  # to find alya IDs
    """
    logger.info(f"Aligning alya {alya_id=}")

    try:
        from src.services.alignment_pipeline import AlignmentPipeline

        pipeline = AlignmentPipeline()
        alignment_run, pasuk_alignments = pipeline.align_by_alya(alya_id)

        click.echo(f"Alignment complete (run_id={alignment_run.id})")
        click.echo(f"  Verses: {len(pasuk_alignments)}")
        click.echo(f"  Quality: {alignment_run.alignment_quality:.2f}")

    except TorahSyncError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(2)


# Edited by Claude Opus 4.6 — align entire playlist
@cli.command("align-playlist")
@click.argument("playlist_name", type=str)
def align_playlist_cmd(playlist_name: str):
    """Align all alyot/chapters of a parasha or megillah.

    PLAYLIST_NAME is the Hebrew name (e.g., "שיר השירים", "האזינו").

    Example:
        torah-sync align-playlist "שיר השירים"
        torah-sync align-playlist האזינו
    """
    logger.info(f"Aligning playlist {playlist_name=}")

    try:
        from src.services.alignment_pipeline import AlignmentPipeline

        pipeline = AlignmentPipeline()
        results = pipeline.align_playlist(playlist_name)

        click.echo(f"\nAligned {len(results)} alyot for '{playlist_name}':")
        for alignment_run, pasuk_alignments in results:
            click.echo(
                f"  run_id={alignment_run.id}  "
                f"verses={len(pasuk_alignments)}  "
                f"quality={alignment_run.alignment_quality:.2f}"
            )

    except TorahSyncError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(2)


@cli.command()
@click.argument("alya_id", type=int, required=False)
def correct(alya_id: int | None):
    """Launch the marimo alignment correction app.

    Optionally pass an ALYA_ID to pre-select an alya for correction.

    Example:
        torah-sync correct
        torah-sync correct 1
    """
    import subprocess

    app_path = Path(__file__).parent.parent / "apps" / "alignment_editor.py"
    if not app_path.exists():
        click.echo(f"✗ Correction app not found: {app_path}", err=True)
        sys.exit(1)

    cmd = ["uv", "run", "--extra", "app", "marimo", "run", str(app_path)]
    if alya_id is not None:
        cmd.extend(["--", f"--alya-id={alya_id}"])

    click.echo(f"Launching correction app...")
    subprocess.run(cmd)


@cli.command()
@click.argument("alya_id", type=int)
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output directory")
def render(alya_id: int, output: Path | None):
    """Render video from finalized alignment data in DuckDB.

    ALYA_ID is the alya to render (from 'torah-sync status').

    Example:
        torah-sync render 1
    """
    logger.info(f"Rendering video for {alya_id=}")

    try:
        from src.services.render_pipeline import RenderPipeline

        pipeline = RenderPipeline()
        video = pipeline.render(alya_id, output_dir=output)

        click.echo(f"✓ Video rendered: {video.file_path}")
        click.echo(f"  Duration: {video.duration_seconds:.1f}s")

    except TorahSyncError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(2)


@cli.command()
@click.argument("parasha_name", type=str)
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output directory")
def render_playlist(parasha_name: str, output: Path | None):
    """Render all alyot for a parasha/playlist.

    PARASHA_NAME is the name of the parasha (e.g., "האזינו").

    Example:
        torah-sync render-playlist האזינו
    """
    logger.info(f"Rendering playlist: {parasha_name=}")

    try:
        from src.repositories.playlist_repo import PlaylistRepository
        from src.repositories.alya_repo import AlyaRepository
        from src.services.render_pipeline import RenderPipeline

        # Find the playlist by name
        playlist_repo = PlaylistRepository()
        playlists = playlist_repo.list_all()
        playlist = next((p for p in playlists if parasha_name in p.name), None)

        if not playlist:
            click.echo(f"✗ Playlist '{parasha_name}' not found", err=True)
            click.echo(f"\nAvailable playlists:")
            for p in playlists:
                click.echo(f"  - {p.name}")
            sys.exit(1)

        # Get all alyot for this playlist
        alya_repo = AlyaRepository()
        alyot = alya_repo.list_by_playlist(playlist.id)

        if not alyot:
            click.echo(f"✗ No alyot found for '{playlist.name}'", err=True)
            sys.exit(1)

        click.echo(f"📖 Rendering {len(alyot)} alyot for {playlist.name}")

        # Render each alya
        pipeline = RenderPipeline()
        rendered_count = 0
        failed_count = 0

        for alya in alyot:
            try:
                click.echo(f"\n  Rendering {alya.name} (id={alya.id})...")
                video = pipeline.render(alya.id, output_dir=output)
                click.echo(f"  ✓ {video.file_path} ({video.duration_seconds:.1f}s)")
                rendered_count += 1
            except Exception as e:
                click.echo(f"  ✗ Failed: {e}", err=True)
                failed_count += 1
                logger.exception(f"Failed to render {alya.id=}")

        # Summary
        click.echo(f"\n{'='*60}")
        click.echo(f"Rendered: {rendered_count}/{len(alyot)}")
        if failed_count > 0:
            click.echo(f"Failed: {failed_count}")
            sys.exit(1)

    except TorahSyncError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(2)


@cli.command()
def status():
    """Show alignment status for all alyot in DuckDB.

    Example:
        torah-sync status
    """
    from src.repositories.alya_repo import AlyaRepository
    from src.repositories.alignment_repo import AlignmentRunRepository
    from src.repositories.alya_audio_repo import AlyaAudioRepository
    from src.repositories.playlist_repo import PlaylistRepository

    playlist_repo = PlaylistRepository()
    alya_repo = AlyaRepository()
    audio_repo = AlyaAudioRepository()
    run_repo = AlignmentRunRepository()

    playlists = playlist_repo.list_all()
    if not playlists:
        click.echo("No playlists found. Run 'torah-sync align' first.")
        return

    for playlist in playlists:
        click.echo(f"\n📖 {playlist.name} ({playlist.book})")
        alyot = alya_repo.list_by_playlist(playlist.id)

        for alya in alyot:
            audio = audio_repo.get_by_alya(alya.id)
            run = run_repo.get_latest_by_audio(audio.id) if audio else None

            state_icon = {
                "pending": "⏳", "aligning": "🔄", "aligned": "✅",
                "rendering": "🎬", "completed": "🎉", "failed": "❌",
            }.get(alya.state.value, "❓")

            quality = f" quality={run.alignment_quality:.2f}" if run else ""
            corrected = " [corrected]" if run and run.manually_corrected else ""

            click.echo(f"  {state_icon} {alya.name} (id={alya.id}, state={alya.state.value}{quality}{corrected})")


@cli.command()
@click.option("--track", is_flag=True, default=False, help="Log results to MLflow")
def evaluate(track: bool):
    """Evaluate alignment accuracy using manually corrected ground truth.

    Compares predicted timestamps against manual corrections stored in DuckDB
    to measure alignment quality (MAE, bias, tolerance percentages).

    Example:
        torah-sync evaluate
        torah-sync evaluate --track
    """
    # Edited by Claude Opus 4.6
    from src.services.alignment.evaluator import evaluate_alignment, format_metrics_report

    metrics = evaluate_alignment()
    report = format_metrics_report(metrics)
    click.echo(report)

    if track:
        from src.services.alignment.tracker import is_tracking_available, log_experiment_run

        if not is_tracking_available():
            click.echo("MLflow not installed. Install with: uv pip install torah-sync[tracking]")
            return

        run_id = log_experiment_run(metrics=metrics, report=report)
        if run_id:
            click.echo(f"Logged to MLflow ({run_id=})")
            click.echo("  View: mlflow ui --backend-store-uri mlruns")


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output directory")
def process(audio_file: Path, output: Path | None):
    """Run full pipeline: align + render (legacy compat).

    Example:
        torah-sync process "data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4"
    """
    logger.info(f"Processing audio file {audio_file.name}")

    try:
        validate_audio_file(audio_file)

        from src.services.alignment_pipeline import AlignmentPipeline
        from src.services.render_pipeline import RenderPipeline

        # Phase 1: Align
        align_pipeline = AlignmentPipeline()
        alignment_run, pasuk_alignments = align_pipeline.align(audio_file)
        click.echo(f"✓ Aligned {len(pasuk_alignments)} verses (quality={alignment_run.alignment_quality:.2f})")

        # Phase 3: Render (skip Phase 2 correction)
        # Need alya_id from the alignment data
        from src.repositories.alya_audio_repo import AlyaAudioRepository

        alya_audio = AlyaAudioRepository().get_by_id(alignment_run.alya_audio_id)
        render_pipeline = RenderPipeline()
        video = render_pipeline.render(alya_audio.alya_id, output_dir=output)

        click.echo(f"✓ Video created: {video.file_path}")
        click.echo(f"  Duration: {video.duration_seconds:.1f}s")

    except TorahSyncError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(2)


# YouTube integration commands (added by Claude Sonnet 4.5)
from src.cli.youtube_commands import youtube
cli.add_command(youtube)


if __name__ == "__main__":
    cli()
