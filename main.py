import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv


load_dotenv()

# ---- Config via env vars ----
# Path to service account JSON key
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
# Your spreadsheet id (the long id in the sheet URL)
SHEET_ID = os.getenv("SHEET_ID", "")
# Default range (can override per request)
DEFAULT_RANGE = os.getenv("DEFAULT_RANGE", "Sheet1!A:Z")

if not GOOGLE_APPLICATION_CREDENTIALS or not SHEET_ID:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS and SHEET_ID must be set")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

app = FastAPI(title="Sheets Live API")

# If your Wix site is at a specific domain, replace "*" with that domain for tighter security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

def get_sheets_service():
    if not GOOGLE_APPLICATION_CREDENTIALS:
        raise HTTPException(status_code=500, detail="GOOGLE_APPLICATION_CREDENTIALS env var is not set")
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS,
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/sheet")
def read_sheet(
    range_: str = Query(DEFAULT_RANGE, alias="range"),
    header_row: int = Query(1, ge=1, description="Which row contains headers (1-indexed). Set 0 to disable header mapping."),
    value_render_option: str = Query("UNFORMATTED_VALUE", pattern="^(FORMATTED_VALUE|UNFORMATTED_VALUE|FORMULA)$"),
) -> Dict[str, Any]:
    """
    Reads Google Sheet values live and returns JSON.
    - If header_row >= 1, returns rows as objects keyed by header names.
    - If header_row == 0, returns raw 2D array.
    """
    if not SHEET_ID:
        raise HTTPException(status_code=500, detail="SHEET_ID env var is not set")

    try:
        service = get_sheets_service()
        resp = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=SHEET_ID,
                range=range_,
                valueRenderOption=value_render_option,
            )
            .execute()
        )
        values: List[List[Any]] = resp.get("values", [])
        if not values:
            return {"range": range_, "rows": [], "raw": []}

        if header_row == 0:
            return {"range": range_, "raw": values}

        # Convert header_row (1-indexed) to list index
        header_idx = header_row - 1
        if header_idx >= len(values):
            return {"range": range_, "rows": [], "raw": values}

        headers = [str(h).strip() for h in values[header_idx]]
        data_rows = values[header_idx + 1 :]

        def row_to_obj(row: List[Any]) -> Dict[str, Any]:
            obj: Dict[str, Any] = {}
            for i, key in enumerate(headers):
                if not key:
                    key = f"col_{i+1}"
                obj[key] = row[i] if i < len(row) else None
            return obj

        mapped = [row_to_obj(r) for r in data_rows if any(cell != "" for cell in r)]
        return {"range": range_, "rows": mapped, "headers": headers}

    except HttpError as e:
        raise HTTPException(status_code=502, detail=f"Google Sheets API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
