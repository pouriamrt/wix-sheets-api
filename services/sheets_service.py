"""Google Sheets service for reading spreadsheet data."""

from typing import Any, Dict, List

from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import get_settings


class SheetsService:
    """Service for interacting with Google Sheets API."""

    def __init__(self):
        """Initialize the sheets service."""
        self.settings = get_settings()
        self._service = None

    def _get_service(self):
        """Get or create the Google Sheets service instance."""
        if self._service is None:
            if not self.settings.google_application_credentials:
                raise HTTPException(
                    status_code=500,
                    detail="GOOGLE_APPLICATION_CREDENTIALS env var is not set",
                )
            creds = service_account.Credentials.from_service_account_file(
                self.settings.google_application_credentials,
                scopes=self.settings.scopes,
            )
            self._service = build(
                "sheets", "v4", credentials=creds, cache_discovery=False
            )
        return self._service

    def read_sheet(
        self,
        range_: str,
        value_render_option: str = "UNFORMATTED_VALUE",
    ) -> List[List[Any]]:
        """
        Read values from a Google Sheet.

        Args:
            range_: The A1 notation range to read (e.g., "Sheet1!A:Z")
            value_render_option: How to render values (FORMATTED_VALUE, UNFORMATTED_VALUE, FORMULA)

        Returns:
            A 2D list of values from the sheet

        Raises:
            HTTPException: If there's an error reading from the sheet
        """
        if not self.settings.sheet_id:
            raise HTTPException(status_code=500, detail="SHEET_ID env var is not set")

        try:
            service = self._get_service()
            resp = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self.settings.sheet_id,
                    range=range_,
                    valueRenderOption=value_render_option,
                )
                .execute()
            )
            return resp.get("values", [])
        except HttpError as e:
            raise HTTPException(status_code=502, detail=f"Google Sheets API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def process_sheet_data(
        self,
        values: List[List[Any]],
        header_row: int = 1,
    ) -> Dict[str, Any]:
        """
        Process raw sheet values into structured data.

        Args:
            values: Raw 2D array of sheet values
            header_row: Which row contains headers (1-indexed). Set 0 to disable header mapping.

        Returns:
            Dictionary with processed data (rows, headers, raw values)
        """
        if not values:
            return {"rows": [], "raw": []}

        if header_row == 0:
            return {"raw": values}

        # Convert header_row (1-indexed) to list index
        header_idx = header_row - 1
        if header_idx >= len(values):
            return {"rows": [], "raw": values}

        headers = [str(h).strip() for h in values[header_idx]]
        data_rows = values[header_idx + 1 :]

        def row_to_obj(row: List[Any]) -> Dict[str, Any]:
            """Convert a row list to a dictionary keyed by headers."""
            obj: Dict[str, Any] = {}
            for i, key in enumerate(headers):
                if not key:
                    key = f"col_{i + 1}"
                obj[key] = row[i] if i < len(row) else None
            return obj

        mapped = [row_to_obj(r) for r in data_rows if any(cell != "" for cell in r)]
        return {"rows": mapped, "headers": headers, "raw": values}

    def update_sheet(self, range_: str, value: List[List[Any]]):
        """Append values to the end of the sheet."""
        try:
            service = self._get_service()
            service.spreadsheets().values().append(
                spreadsheetId=self.settings.sheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": value},
            ).execute()
            return {"message": "Sheet updated successfully", "range": range_}
        except HttpError as e:
            raise HTTPException(status_code=502, detail=f"Google Sheets API error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Global service instance
_sheets_service: SheetsService | None = None


def get_sheets_service() -> SheetsService:
    """Get or create the global sheets service instance."""
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = SheetsService()
    return _sheets_service
