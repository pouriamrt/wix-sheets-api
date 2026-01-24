"""Main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router
from config import get_settings

# Initialize settings to validate environment variables on startup
get_settings()

app = FastAPI(title="Sheets Live API")

# If your Wix site is at a specific domain, replace "*" with that domain for tighter security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
