# Edited by Claude Opus 4.6
"""Playlist model representing a YouTube playlist for a Parasha or Megillah."""

from datetime import datetime

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PlaylistType(str, Enum):
    """Type of playlist: parasha (Torah portion) or megillah (scroll)."""

    PARASHA = "parasha"
    MEGILLAH = "megillah"


class Playlist(BaseModel):
    """A YouTube playlist grouping all Aliyot of a Parasha or chapters of a Megillah.

    Attributes:
        id: Database primary key (None before insert)
        name: Name in Hebrew (e.g., "האזינו" or "שיר השירים")
        book: Book name (e.g., "Deuteronomy", "Song of Songs")
        playlist_type: Type of reading (parasha or megillah)
        chapter_start: Starting chapter number
        verse_start: Starting verse number
        chapter_end: Ending chapter number
        verse_end: Ending verse number
        youtube_playlist_id: YouTube playlist ID (set after upload)
        created_at: Record creation timestamp
    """

    id: int | None = Field(default=None, description="Database PK")
    name: str = Field(..., min_length=1, description="Name in Hebrew")
    book: str = Field(..., min_length=1, description="Book name")
    playlist_type: PlaylistType = Field(
        default=PlaylistType.PARASHA, description="Type: parasha or megillah"
    )
    chapter_start: int = Field(..., gt=0, description="Starting chapter number")
    verse_start: int = Field(..., gt=0, description="Starting verse number")
    chapter_end: int = Field(..., gt=0, description="Ending chapter number")
    verse_end: int = Field(..., gt=0, description="Ending verse number")
    youtube_playlist_id: str | None = Field(default=None, description="YouTube playlist ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")

    @field_validator("chapter_end")
    @classmethod
    def validate_chapter_order(cls, v: int, info) -> int:
        """Validate chapter_start <= chapter_end."""
        if "chapter_start" in info.data and v < info.data["chapter_start"]:
            raise ValueError(
                f"chapter_end ({v}) must be >= chapter_start ({info.data['chapter_start']})"
            )
        return v
