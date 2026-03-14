# ─── Config ───────────────────────────────────────────────
PROJECT  := wix-project-485002
REGION   := us-east1
REPO     := wix-proj-repo
IMAGE    := wix-nabis-api
SERVICE  := wix-fastapi-nabis

REGISTRY := $(REGION)-docker.pkg.dev/$(PROJECT)/$(REPO)/$(IMAGE)
TAG      ?= latest
ENV_FILE ?= .env

# ─── Local ────────────────────────────────────────────────
.PHONY: install dev lint docker-up docker-down

install:                ## Install dependencies
	uv sync

dev:                    ## Run locally with hot reload
	uvicorn main:app --reload --port 8000

lint:                   ## Lint and format (Ruff)
	pre-commit run --all-files

docker-up:              ## Start with Docker Compose
	docker compose up --build -d

docker-down:            ## Stop Docker Compose
	docker compose down

# ─── Deploy ───────────────────────────────────────────────
.PHONY: build push deploy deploy-all

build:                  ## Build image via Cloud Build
	gcloud builds submit --config cloudbuild.yaml --project $(PROJECT)

push: build             ## Alias: build already pushes to Artifact Registry

# Generate a YAML env-vars file from .env, stripping comments, quotes,
# and GOOGLE_APPLICATION_CREDENTIALS (Cloud Run uses ADC instead).
.env.yaml: $(ENV_FILE)
	@grep -v '^\s*\#' $(ENV_FILE) 2>/dev/null \
		| grep -v '^\s*$$' \
		| grep -v '^GOOGLE_APPLICATION_CREDENTIALS' \
		| grep '=' \
		| sed 's/"//g' \
		| sed 's/=\(.*\)/: "\1"/' > .env.yaml

deploy: .env.yaml       ## Deploy image to Cloud Run with .env vars
	gcloud run deploy $(SERVICE) --image $(REGISTRY):$(TAG) --region $(REGION) --project $(PROJECT) --allow-unauthenticated --env-vars-file .env.yaml

deploy-all: build deploy ## Build + deploy in one step

# ─── Inspect ──────────────────────────────────────────────
.PHONY: logs status url

logs:                   ## Tail Cloud Run logs
	gcloud run services logs tail $(SERVICE) --region $(REGION) --project $(PROJECT)

status:                 ## Show Cloud Run service status
	gcloud run services describe $(SERVICE) --region $(REGION) --project $(PROJECT) --format="table(status.url, status.conditions.type, status.conditions.status)"

url:                    ## Print the service URL
	@gcloud run services describe $(SERVICE) --region $(REGION) --project $(PROJECT) --format="value(status.url)"

# ─── Help ─────────────────────────────────────────────────
.PHONY: help
help:                   ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
