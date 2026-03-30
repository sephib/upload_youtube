# Edited by Claude Opus 4.6
"""Alya model representing an Aliyah (Torah portion) or chapter (Megillah)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# Valid Aliyah names in Hebrew (Torah portions)
VALID_ALYA_NAMES_TORAH = {
    "ראשון",  # Rishon (First)
    "שני",  # Sheni (Second)
    "שלישי",  # Shlishi (Third)
    "רביעי",  # Revi'i (Fourth)
    "חמישי",  # Chamishi (Fifth)
    "שישי",  # Shishi (Sixth)
    "שביעי",  # Shevi'i (Seventh)
    "מפטיר",  # Maftir
    "הפטרה",  # Haftara
}

# Valid chapter names in Hebrew (Megillot)
VALID_ALYA_NAMES_MEGILLAH = {
    "פרק א",
    "פרק ב",
    "פרק ג",
    "פרק ד",
    "פרק ה",
    "פרק ו",
    "פרק ז",
    "פרק ח",
    "פרק ט",
    "פרק י",
    "פרק יא",
    "פרק יב",
}

VALID_ALYA_NAMES = VALID_ALYA_NAMES_TORAH | VALID_ALYA_NAMES_MEGILLAH


class AlyaState(str, Enum):
    """State transitions for Alya processing."""

    PENDING = "pending"
    ALIGNING = "aligning"
    ALIGNED = "aligned"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class Alya(BaseModel):
    """An Aliyah within a Parasha, referencing a Playlist by FK.

    Attributes:
        id: Database primary key (None before insert)
        playlist_id: FK to playlists.id
        name: Aliyah name in Hebrew (e.g., "ראשון")
        order_num: Sequence number within Parasha (1-9)
        state: Current processing state
        created_at: Record creation timestamp
    """

    id: int | None = Field(default=None, description="Database PK")
    playlist_id: int = Field(..., description="FK to playlists.id")
    name: str = Field(..., min_length=1, description="Aliyah name in Hebrew")
    order_num: int = Field(..., ge=1, le=30, description="Sequence number within reading")
    state: AlyaState = Field(default=AlyaState.PENDING, description="Processing state")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")

    @field_validator("name")
    @classmethod
    def validate_alya_name(cls, v: str) -> str:
        """Validate Aliyah name is one of canonical names."""
        if v not in VALID_ALYA_NAMES:
            raise ValueError(
                f"Invalid Alya name: {v}. Must be one of: {', '.join(sorted(VALID_ALYA_NAMES))}"
            )
        return v
