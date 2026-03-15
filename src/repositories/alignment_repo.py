# Edited by Claude Opus 4.6
"""Repository for AlignmentRun entities."""

from src.models.alignment_run import AlignmentRun
from src.repositories.db import get_connection


class AlignmentRunRepository:
    """CRUD operations for the alignment_runs table."""

    def insert(self, run: AlignmentRun) -> AlignmentRun:
        """Insert a new alignment run and return it with the generated id."""
        conn = get_connection()
        result = conn.execute(
            """
            INSERT INTO alignment_runs
                (alya_audio_id, alignment_quality, verse_count, manually_corrected,
                 corrected_at, backup_path, original_quality)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            [
                run.alya_audio_id,
                run.alignment_quality,
                run.verse_count,
                run.manually_corrected,
                run.corrected_at,
                run.backup_path,
                run.original_quality,
            ],
        ).fetchone()
        run.id = result[0]
        return run

    def get_by_id(self, run_id: int) -> AlignmentRun | None:
        """Get an alignment run by id."""
        conn = get_connection()
        row = conn.execute("SELECT * FROM alignment_runs WHERE id = ?", [run_id]).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def get_latest_by_audio(self, alya_audio_id: int) -> AlignmentRun | None:
        """Get the most recent alignment run for an alya audio."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM alignment_runs WHERE alya_audio_id = ? ORDER BY generated_at DESC LIMIT 1",
            [alya_audio_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def list_by_audio(self, alya_audio_id: int) -> list[AlignmentRun]:
        """List all alignment runs for an alya audio."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM alignment_runs WHERE alya_audio_id = ? ORDER BY generated_at DESC",
            [alya_audio_id],
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def list_all(self) -> list[AlignmentRun]:
        """List all alignment runs."""
        conn = get_connection()
        rows = conn.execute("SELECT * FROM alignment_runs ORDER BY id").fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, run: AlignmentRun) -> None:
        """Update an existing alignment run."""
        conn = get_connection()
        conn.execute(
            """
            UPDATE alignment_runs
            SET alya_audio_id = ?, alignment_quality = ?, verse_count = ?,
                manually_corrected = ?, corrected_at = ?, backup_path = ?,
                original_quality = ?
            WHERE id = ?
            """,
            [
                run.alya_audio_id,
                run.alignment_quality,
                run.verse_count,
                run.manually_corrected,
                run.corrected_at,
                run.backup_path,
                run.original_quality,
                run.id,
            ],
        )

    def mark_corrected(self, run: AlignmentRun) -> None:
        # Edited by Claude Opus 4.6 (targeted update avoids DuckDB FK issue)
        """Update only correction fields, avoiding DuckDB FK constraint on full UPDATE."""
        conn = get_connection()
        conn.execute(
            """
            UPDATE alignment_runs
            SET manually_corrected = ?, corrected_at = ?, original_quality = ?
            WHERE id = ?
            """,
            [run.manually_corrected, run.corrected_at, run.original_quality, run.id],
        )

    def delete(self, run_id: int) -> None:
        """Delete an alignment run by id."""
        conn = get_connection()
        conn.execute("DELETE FROM alignment_runs WHERE id = ?", [run_id])

    @staticmethod
    def _row_to_model(row: tuple) -> AlignmentRun:
        """Convert a database row to an AlignmentRun model."""
        return AlignmentRun(
            id=row[0],
            alya_audio_id=row[1],
            alignment_quality=row[2],
            verse_count=row[3],
            manually_corrected=row[4],
            corrected_at=row[5],
            backup_path=row[6],
            original_quality=row[7],
            generated_at=row[8],
        )
