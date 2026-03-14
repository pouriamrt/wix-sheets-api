"""API route handlers."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from config import get_settings
from schemas.sheet_req import (
    SubmitCommentRequest,
    SubmitEntryRequest,
    UpdateSheetRequest,
)
from services import get_sheets_service

router = APIRouter()


def _utc_stamp() -> str:
    """Return the current UTC time as a text-forced string for Google Sheets.

    The leading apostrophe tells the Sheets API (USER_ENTERED mode) to store
    the value as plain text, preventing auto-conversion to a serial number.
    The apostrophe is not displayed in the cell.
    """
    return "'" + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _is_verified(value: Any) -> bool:
    """Check if a cell value represents a verified entry."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().upper() == "TRUE"
    return bool(value)


@router.get("/health")
def health() -> dict[str, bool]:
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
    verified_only: bool = Query(
        True,
        description="If true, only return rows where 'Entry verified' is TRUE.",
    ),
) -> dict[str, Any]:
    """
    Reads Google Sheet values live and returns JSON.
    - If header_row >= 1, returns rows as objects keyed by header names.
    - If header_row == 0, returns raw 2D array.
    - If verified_only is true (default), filters to rows with 'Entry verified' == TRUE.
    """
    settings = get_settings()
    sheets_service = get_sheets_service()
    range_ = range_ or settings.default_range

    try:
        values = sheets_service.read_sheet(range_, value_render_option)
        processed = sheets_service.process_sheet_data(values, header_row)

        if verified_only and header_row >= 1 and "rows" in processed:
            processed["rows"] = [
                row
                for row in processed["rows"]
                if _is_verified(row.get("Entry verified"))
            ]

        return {"range": range_, **processed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sheet")
def update_sheet(request: UpdateSheetRequest) -> dict[str, Any]:
    """Append the given values to the end of the sheet. Request body: { \"range\": \"...\", \"value\": [[...]] }."""
    try:
        settings = get_settings()
        sheets_service = get_sheets_service()
        range_ = request.range or settings.default_range
        sheets_service.update_sheet(range_, request.value)
        return {"message": "Sheet updated successfully", "range": range_}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entry")
def submit_entry(request: SubmitEntryRequest) -> dict[str, Any]:
    """
    Submit a new entry to the 'New Entries to Verify' tab.

    Accepts key-value data matching column headers. Automatically adds a
    'Date Stamp' timestamp and sets 'Entry verified' to False.
    """
    settings = get_settings()
    sheets_service = get_sheets_service()

    entry_values = sheets_service.read_sheet(settings.entries_range)
    if not entry_values:
        raise HTTPException(
            status_code=500,
            detail="'New Entries to Verify' tab has no header row.",
        )

    headers = [str(h).strip() for h in entry_values[0]]

    data = {
        **request.data,
        "Entry verified": "False",
        "Date Stamp": _utc_stamp(),
    }
    row = [data.get(h, "") for h in headers]

    sheets_service.update_sheet(settings.entries_range, [row])
    return {
        "message": "Entry submitted for verification",
        "range": settings.entries_range,
    }


@router.post("/comment")
def submit_comment(request: SubmitCommentRequest) -> dict[str, Any]:
    """
    Submit a standalone comment to the 'Comments' tab.

    Comments are independent of entries and include an automatic date stamp.
    """
    settings = get_settings()
    sheets_service = get_sheets_service()

    row = [_utc_stamp(), request.comment]

    sheets_service.update_sheet(settings.comments_range, [row])
    return {
        "message": "Comment submitted successfully",
        "range": settings.comments_range,
    }
