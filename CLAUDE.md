# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend that reads/writes Google Sheets in real time, consumed by a Wix frontend (Velo + embedded HTML component) and deployed on Google Cloud Run.

## Commands

```bash
# Install dependencies
uv sync

# Run locally (with hot reload)
uvicorn main:app --reload --port 8000

# Run with Docker
docker compose up --build

# Lint and format (Ruff via pre-commit)
pre-commit run --all-files

# Deploy to GCP
gcloud builds submit --config cloudbuild.yaml
gcloud run deploy wix-fastapi-nabis --image us-east1-docker.pkg.dev/wix-project-485002/wix-proj-repo/wix-nabis-api:latest --allow-unauthenticated
```

## Architecture

**Layered modular structure with singletons:**

- **`main.py`** — FastAPI app entry point. Configures CORS (all origins), uses `ORJSONResponse` as default response class, includes the API router, and validates settings at startup.
- **`api/routes.py`** — Five endpoints: `GET /health`, `GET /sheet` (read with optional header mapping, `value_render_option`, and `verified_only` filter), `POST /sheet` (generic append), `POST /entry` (submit to "New Entries to Verify" tab with auto date stamp), `POST /comment` (standalone comment to "Comments" tab with auto date stamp).
- **`config/settings.py`** — Loads env vars (`SHEET_ID`, `DEFAULT_RANGE`, `ENTRIES_RANGE`, `COMMENTS_RANGE`, `GOOGLE_APPLICATION_CREDENTIALS`) via `python-dotenv`. Singleton via `get_settings()`.
- **`schemas/sheet_req.py`** — Pydantic request models: `UpdateSheetRequest` (POST /sheet), `SubmitEntryRequest` (POST /entry, key-value data dict), `SubmitCommentRequest` (POST /comment, comment string).
- **`services/sheets_service.py`** — Google Sheets API client with lazy initialization. Two auth modes: service account JSON (local/Docker) or Application Default Credentials (Cloud Run). Singleton via `get_sheets_service()`.
- **`html/`** — Wix-embeddable frontend (not served by FastAPI):
  - `index.html` — Filterable card UI rendered inside a Wix HTML embed (`#html1`)
  - `Wix_page.js` — Velo page code for the main display page; fetches data from the API and sends it to `index.html` via `postMessage`; auto-reloads every 2 minutes
  - `form_submit.js` — Velo page code for the submission/feedback page; POSTs entries to `/entry` (all fields optional) and standalone comments to `/comment`

**Package convention:** Each Python package (`api/`, `config/`, `services/`) has an `__init__.py` that re-exports its public API (e.g., `from config import get_settings`).

### Data flow

```
Wix Velo page code ($w)
  ↕ postMessage
Embedded HTML (index.html in #html1)
  ↕ fetch
FastAPI backend (Cloud Run)
  ↕ Google Sheets API v4
Google Sheet (source of truth)
```

The Wix page code (`Wix_page.js`) fetches JSON from the FastAPI backend, then pushes it into the embedded HTML component via `postMessage`. The HTML component renders filterable cards and communicates filter state back to Velo. The form page (`form_submit.js`) sends entries to `POST /entry` (routed to "New Entries to Verify" tab with auto date stamp) and standalone comments to `POST /comment` (routed to "Comments" tab). `GET /sheet` defaults to `verified_only=true`, so only verified entries appear on the website.

### Google Sheet tabs

| Tab | Purpose |
|-----|---------|
| `Sheet1` | Live verified directory (displayed on website) |
| `New Entries to Verify` | Newly submitted entries awaiting review (columns: Date Stamp, Org Name, Country, …, Entry verified, MM Comments) |
| `Comments` | Standalone comments (columns: Date Stamp, Comments) |
| `glossary` | Reference glossary |

## Key Technical Details

- **Python 3.13** required (`.python-version`)
- **uv** for dependency management (`uv sync`, `uv.lock`)
- **No test suite exists** — no pytest or test files
- **Pre-commit hooks** use Ruff v0.14.4 for both linting (`ruff-check --fix`) and formatting (`ruff-format`)
- **Google Sheets auth**: set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON path for local dev; omit on Cloud Run to use ADC
- **`GET /sheet` header_row param**: 0 returns raw 2D array, >=1 uses that row as object keys. `verified_only` param (default true) filters to rows where "Entry verified" is TRUE
- Docker runs as non-root user (`app:app`), port 8080 in container, overridden to port 8000 via docker-compose `ports` mapping
- **GitHub Actions**: `claude.yml` (responds to `@claude` mentions on issues/PRs) and `claude-code-review.yml` (auto-reviews PRs on open/sync)

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SHEET_ID` | Yes | `""` | Google Spreadsheet ID |
| `DEFAULT_RANGE` | No | `Sheet1!A:Z` | Default A1 notation range |
| `ENTRIES_RANGE` | No | `New Entries to Verify!A:M` | Range for unverified entry submissions |
| `COMMENTS_RANGE` | No | `Comments!A:B` | Range for standalone comments |
| `GOOGLE_APPLICATION_CREDENTIALS` | No (on GCP) | `""` | Path to service account JSON |

Copy `.env.example` to `.env` for local development.
