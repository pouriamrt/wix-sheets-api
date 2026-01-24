"""API route handlers."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from config import get_settings
from services import get_sheets_service
from schemas.sheet_req import UpdateSheetRequest

router = APIRouter()


@router.get("/health")
def health() -> Dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}


@router.get("/sheet")
def read_sheet(
    range_: str = Query(
        default=None,
        alias="range",
        description="A1 notation range (e.g., Sheet1!A:Z)",
    ),
    header_row: int = Query(
        1,
        ge=0,
        description="Which row contains headers (1-indexed). Set 0 to disable header mapping.",
    ),
    value_render_option: str = Query(
        "UNFORMATTED_VALUE",
        pattern="^(FORMATTED_VALUE|UNFORMATTED_VALUE|FORMULA)$",
    ),
) -> Dict[str, Any]:
    """
    Reads Google Sheet values live and returns JSON.
    - If header_row >= 1, returns rows as objects keyed by header names.
    - If header_row == 0, returns raw 2D array.
    """
    settings = get_settings()
    sheets_service = get_sheets_service()

    # Use default range if not provided
    if range_ is None:
        range_ = settings.default_range

    try:
        values = sheets_service.read_sheet(range_, value_render_option)
        processed = sheets_service.process_sheet_data(values, header_row)

        result = {"range": range_}
        result.update(processed)

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sheet")
def update_sheet(request: UpdateSheetRequest) -> Dict[str, Any]:
    """Append the given values to the end of the sheet. Request body: { \"range\": \"...\", \"value\": [[...]] }."""
    try:
        settings = get_settings()
        sheets_service = get_sheets_service()
        range_ = request.range if request.range is not None else settings.default_range
        sheets_service.update_sheet(range_, request.value)
        return {"message": "Sheet updated successfully", "range": range_}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
