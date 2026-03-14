"""Pydantic request models for sheet-related endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from config import get_settings

settings = get_settings()


class UpdateSheetRequest(BaseModel):
    """Request body for updating sheet values."""

    range: str | None = Field(
        default_factory=lambda: settings.default_range,
        example=settings.default_range,
        description="A1 notation range (e.g., Sheet1!A:Z). Omit to use the configured default.",
    )
    value: list[list[Any]] = Field(
        default_factory=list,
        description="2D list of values to write to the sheet.",
    )


class SubmitEntryRequest(BaseModel):
    """Request body for submitting a new entry to the 'New Entries to Verify' tab."""

    data: dict[str, Any] = Field(
        ...,
        description="Key-value pairs matching sheet column headers (e.g., 'Organization Name', 'Country').",
    )


class SubmitCommentRequest(BaseModel):
    """Request body for submitting a standalone comment."""

    comment: str = Field(..., min_length=1, description="The comment text to submit.")
