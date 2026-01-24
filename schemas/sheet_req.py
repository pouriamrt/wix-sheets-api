from pydantic import BaseModel, Field
from typing import List, Any
from config import get_settings


settings = get_settings()


class UpdateSheetRequest(BaseModel):
    """Request body for updating sheet values."""

    range: str | None = Field(
        default_factory=lambda: settings.default_range,
        example=settings.default_range,
        description="A1 notation range (e.g., Sheet1!A:Z). Omit to use the configured default.",
    )
    value: List[List[Any]] = Field(
        default_factory=list,
        description="2D list of values to write to the sheet.",
    )
