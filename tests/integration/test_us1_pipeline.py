# Edited by Claude Opus 4.6 (rewritten for 3-phase pipeline)
"""Integration tests for the 3-phase pipeline: align -> correct -> render.

Tests require a sample audio file and aeneas to be installed.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def sample_audio_file():
    """Path to sample Torah reading audio file (Haazinu Rishon)."""
    audio_path = Path("data/audio/פרשת האזינו - ראשון - נוסח אשכנז.mp4")
    if not audio_path.exists():
        pytest.skip(f"Sample audio file not found: {audio_path}")
    return audio_path


@pytest.mark.integration
def test_align_command(sample_audio_file):
    """Test 'torah-sync align' produces alignment data in DuckDB."""
    result = subprocess.run(
        ["uv", "run", "torah-sync", "align", str(sample_audio_file)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, (
        f"Align failed (exit {result.returncode})\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "Alignment complete" in result.stdout


@pytest.mark.integration
def test_status_command():
    """Test 'torah-sync status' shows alignment status."""
    result = subprocess.run(
        ["uv", "run", "torah-sync", "status"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"Status failed (exit {result.returncode})\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


@pytest.mark.integration
def test_process_command_legacy_compat(sample_audio_file):
    """Test 'torah-sync process' runs align + render end-to-end."""
    result = subprocess.run(
        ["uv", "run", "torah-sync", "process", str(sample_audio_file)],
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, (
        f"Process failed (exit {result.returncode})\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "Video created" in result.stdout
