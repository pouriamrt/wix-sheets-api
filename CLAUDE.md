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
- **`api/routes.py`** — Three endpoints: `GET /health`, `GET /sheet` (read with optional header mapping), `POST /sheet` (append rows).
- **`config/settings.py`** — Loads env vars (`SHEET_ID`, `DEFAULT_RANGE`, `GOOGLE_APPLICATION_CREDENTIALS`) via `python-dotenv`. Singleton via `get_settings()`.
- **`schemas/sheet_req.py`** — Pydantic request model `UpdateSheetRequest` for POST /sheet.
- **`services/sheets_service.py`** — Google Sheets API client with lazy initialization. Two auth modes: service account JSON (local/Docker) or Application Default Credentials (Cloud Run). Singleton via `get_sheets_service()`.
- **`html/`** — Wix-embeddable frontend (not served by FastAPI). `index.html` is a filterable card UI communicating with Wix via `postMessage`. `Wix_page.js` is Velo page code.

## Key Technical Details

- **Python 3.13** required (`.python-version`)
- **uv** for dependency management (`uv sync`, `uv.lock`)
- **No test suite exists** — no pytest or test files
- **Pre-commit hooks** use Ruff v0.14.4 for both linting (`ruff-check --fix`) and formatting (`ruff-format`)
- **Google Sheets auth**: set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON path for local dev; omit on Cloud Run to use ADC
- **`GET /sheet` header_row param**: 0 returns raw 2D array, >=1 uses that row as object keys
- Docker runs as non-root user (`app:app`), port 8080 in container, port 8000 via docker-compose locally

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SHEET_ID` | Yes | `""` | Google Spreadsheet ID |
| `DEFAULT_RANGE` | No | `Sheet1!A:Z` | Default A1 notation range |
| `GOOGLE_APPLICATION_CREDENTIALS` | No (on GCP) | `""` | Path to service account JSON |

Copy `.env.example` to `.env` for local development.
