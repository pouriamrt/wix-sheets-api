# Wix Backend — Sheets Live API

A **FastAPI** backend that reads and writes **Google Sheets** in real time. Designed to be consumed by Wix (or any frontend) and deployed on **Google Cloud Run**.

---

## Features

- **Read sheet data** — `GET /sheet` returns Google Sheet values as JSON (with optional header-based object mapping)
- **Write sheet data** — `POST /sheet` appends rows to a sheet
- **Health check** — `GET /health` for load balancers and readiness probes
- **CORS** — Configured for cross-origin requests (e.g. from Wix)
- **Cloud Run–ready** — Uses Application Default Credentials (ADC) when `GOOGLE_APPLICATION_CREDENTIALS` is not set

---

## Project Structure

```
├── api/
│   └── routes.py          # FastAPI route handlers
├── config/
│   └── settings.py        # Environment-based settings
├── schemas/
│   └── sheet_req.py       # Pydantic models for requests
├── services/
│   └── sheets_service.py  # Google Sheets API integration
├── html/                  # Optional static/test pages
├── main.py                # App entry point
├── Dockerfile             # Container image for Cloud Run / Docker
├── cloudbuild.yaml        # Google Cloud Build config
├── docker-compose.yml     # Local Docker runs
└── pyproject.toml         # Dependencies (uv)
```

---

## Prerequisites

- **Python 3.13+** (see `.python-version`)
- **Google Cloud project** with Sheets API and (for Cloud Run) the APIs listed below
- **Google Sheet**:
  - Create a sheet and note its **Sheet ID** (from the URL: `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`).
  - For a **service account** (local/Docker): share the sheet with the service account email (e.g. `xxx@wix-project-485002.iam.gserviceaccount.com`) as *Editor*.
  - For **Cloud Run**: the Cloud Run service account must have access to the sheet (or use a Workload Identity–linked SA with Sheets access).

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SHEET_ID` | Yes (for /sheet) | Google Spreadsheet ID |
| `DEFAULT_RANGE` | No | A1 range when `range` is omitted (default: `Sheet1!A:Z`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | No (on GCP) | Path to service account JSON. Omit on Cloud Run to use ADC. |

Copy `.env.example` to `.env` and fill in `SHEET_ID` (and optionally `DEFAULT_RANGE`).

---

## Running Locally

### With uv (recommended)

```bash
# Install uv if needed: https://docs.astral.sh/uv/

uv sync
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Set env (or use .env)
export SHEET_ID=your_sheet_id
export GOOGLE_APPLICATION_CREDENTIALS=./path/to/credentials.json

uvicorn main:app --reload --port 8000
```

- **Health:** http://localhost:8000/health  
- **Docs:** http://localhost:8000/docs  

### With Docker Compose

1. Create `.env` with `SHEET_ID` (and optionally `DEFAULT_RANGE`).
2. Place your service account JSON at `./keys/wix-project-485002-df6702b3ed76.json` (or adjust the `volumes` path in `docker-compose.yml`).
3. Share the Google Sheet with the service account email as Editor.

```bash
docker compose up --build
```

App runs on port **8000**.

---

## API Reference

### `GET /health`

Returns `{"ok": true}`. Use for load balancers and readiness checks.

---

### `GET /sheet`

Reads values from the configured Google Sheet.

| Query | Type | Default | Description |
|-------|------|---------|-------------|
| `range` | string | `DEFAULT_RANGE` | A1 notation (e.g. `Sheet1!A:Z`) |
| `header_row` | int | `1` | Row (1‑indexed) with headers. Use `0` for raw 2D array. |
| `value_render_option` | string | `UNFORMATTED_VALUE` | `FORMATTED_VALUE`, `UNFORMATTED_VALUE`, or `FORMULA` |

**Examples:**

- With headers (objects keyed by header names):  
  `GET /sheet?range=Sheet1!A:Z&header_row=1`
- Raw 2D array:  
  `GET /sheet?header_row=0`

**Response (header_row ≥ 1):**  
`{ "range": "...", "rows": [{...}], "headers": [...], "raw": [[...]] }`  

**Response (header_row = 0):**  
`{ "range": "...", "raw": [[...]] }`

---

### `POST /sheet`

Appends rows to the sheet.

**Body:**

```json
{
  "range": "Sheet1!A:Z",
  "value": [["col1", "col2", "col3"], ["a", "b", "c"]]
}
```

- `range`: optional; falls back to `DEFAULT_RANGE` if omitted.
- `value`: 2D array of values; appended as new rows.

**Response:**  
`{ "message": "Sheet updated successfully", "range": "..." }`

---

## Deploying on Google Cloud Platform (GCP)

The following steps use **Cloud Build** to build a Docker image, push it to **Artifact Registry**, and deploy to **Cloud Run**.

### 1. Authenticate and set project

```bash
gcloud auth login
gcloud config set project wix-project-485002
```

### 2. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Create Artifact Registry repository

```bash
gcloud artifacts repositories create wix-proj-repo \
  --repository-format=docker \
  --location=us-east1 \
  --description="Docker images for Cloud Run"
```

### 4. Build and push the image with Cloud Build

From the project root (where `cloudbuild.yaml` lives):

```bash
gcloud builds submit --config cloudbuild.yaml
```

This builds the Dockerfile and pushes:

`us-east1-docker.pkg.dev/wix-project-485002/wix-proj-repo/wix-nabis-api:latest`

### 5. Deploy to Cloud Run

```bash
gcloud run deploy wix-fastapi-nabis \
  --image us-east1-docker.pkg.dev/wix-project-485002/wix-proj-repo/wix-nabis-api:latest \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars SHEET_ID=YOUR_SHEET_ID,DEFAULT_RANGE="Sheet1!A:Z"
```

- Replace `YOUR_SHEET_ID` with your Google Spreadsheet ID.
- Adjust `DEFAULT_RANGE` if needed.
- **Authentication:** `--allow-unauthenticated` makes the service publicly callable. For production, consider `--no-allow-unauthenticated` and IAM or an API gateway.
- **Sheets access:** Ensure the Cloud Run service account (or the one specified with `--service-account`) has access to the Google Sheet (share the sheet with that email as Editor), or use Workload Identity with a custom service account that has access.

### 6. View logs

```bash
gcloud run services logs read wix-fastapi-nabis \
  --region us-east1 \
  --limit 200
```

For live logs:

```bash
gcloud run services logs tail wix-fastapi-nabis --region us-east1
```

---

## GCP summary

| Step | Command / action |
|------|------------------|
| 1. Login & project | `gcloud auth login` then `gcloud config set project wix-project-485002` |
| 2. Enable APIs | `gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com` |
| 3. Create repo | `gcloud artifacts repositories create wix-proj-repo --repository-format=docker --location=us-east1 --description="Docker images for Cloud Run"` |
| 4. Build image | `gcloud builds submit --config cloudbuild.yaml` |
| 5. Deploy | `gcloud run deploy wix-fastapi-nabis --image us-east1-docker.pkg.dev/wix-project-485002/wix-proj-repo/wix-nabis-api:latest --region us-east1 --allow-unauthenticated --set-env-vars SHEET_ID=YOUR_SHEET_ID,DEFAULT_RANGE="Sheet1!A:Z"` |
| 6. Logs | `gcloud run services logs read wix-fastapi-nabis --region us-east1 --limit 200` |

---

## Docker image

The **Dockerfile**:

- Uses `python:3.13-slim`
- Installs dependencies with **uv** from `pyproject.toml` and `uv.lock`
- Expects at runtime: `SHEET_ID`; optionally `GOOGLE_APPLICATION_CREDENTIALS` (omit on Cloud Run to use ADC)
- Sets `DEFAULT_RANGE=Sheet1!A:Z` and `PORT=8080`
- Runs as non-root user
- Starts: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}`

Cloud Run sets `PORT`; the app listens on that port by default.

---

## Security notes

- Do **not** commit `.env` or service account JSON (see `.gitignore`).
- For production, restrict CORS in `main.py` to your Wix (or app) origin instead of `"*"`.
- Prefer `--no-allow-unauthenticated` on Cloud Run and use IAM or an API gateway if the API should not be public.

---

## License

See repository or project metadata.
