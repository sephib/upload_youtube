# Edited by Claude Opus 4.6
"""AlignmentRun model for forced alignment results."""

from datetime import datetime

from pydantic import BaseModel, Field


class AlignmentRun(BaseModel):
    """Result of a forced alignment run for an AlyaAudio.

    Attributes:
        id: Database primary key (None before insert)
        alya_audio_id: FK to alya_audio.id
        alignment_quality: Alignment confidence score (0.0-1.0)
        verse_count: Number of aligned verses
        manually_corrected: Whether this run has been manually corrected
        corrected_at: When last correction was applied
        backup_path: Path to backup of original alignment
        original_quality: Alignment quality before corrections
        generated_at: When alignment was performed
    """

    id: int | None = Field(default=None, description="Database PK")
    alya_audio_id: int = Field(..., description="FK to alya_audio.id")
    alignment_quality: float = Field(..., ge=0.0, le=1.0, description="Alignment confidence score")
    verse_count: int = Field(..., gt=0, description="Number of aligned verses")
    manually_corrected: bool = Field(default=False, description="Has been manually corrected")
    corrected_at: datetime | None = Field(default=None, description="Last correction timestamp")
    backup_path: str | None = Field(default=None, description="Backup of original alignment")
    original_quality: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Quality before corrections"
    )
    generated_at: datetime | None = Field(default=None, description="When alignment was performed")
