# Wix Backend - FastAPI + Google Sheets API
# Requires at runtime: GOOGLE_APPLICATION_CREDENTIALS, SHEET_ID

FROM python:3.13-slim

WORKDIR /app

# Install uv for fast, reproducible dependency installation
RUN pip install --no-cache-dir uv

# Install dependencies from lock file (layer cached when only code changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Use the venv where uvicorn and dependencies are installed
ENV PATH="/app/.venv/bin:$PATH" DEFAULT_RANGE="Sheet1!A:Z" PORT=8080

EXPOSE $PORT

# Run as non-root
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --create-home app && \
    chown -R app:app /app
USER app

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
