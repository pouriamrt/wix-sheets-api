"""Application settings and configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        """Initialize settings from environment variables."""
        self.google_application_credentials: str = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS", ""
        )
        self.sheet_id: str = os.getenv("SHEET_ID", "")
        self.default_range: str = os.getenv("DEFAULT_RANGE", "Sheet1!A:Z")
        self.entries_range: str = os.getenv(
            "ENTRIES_RANGE", "New Entries to Verify!A:M"
        )
        self.comments_range: str = os.getenv("COMMENTS_RANGE", "Comments!A:B")
        self.scopes: list[str] = ["https://www.googleapis.com/auth/spreadsheets"]


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
