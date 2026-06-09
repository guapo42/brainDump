# Brain Dump x The External Lobe — canonical commands.
# These are the commands the pre-flight checklist (docs/working_pattern.md) names.
.PHONY: setup dev check test lint typecheck build imports up down sim fixtures

setup:               ## install both stacks
	cd backend && uv sync
	cd app && npm install

dev:                 ## run the frontend dev server (backend is optional)
	cd app && npm run dev

check: typecheck lint test imports  ## all fast lanes + separation checks

typecheck:
	cd app && npm run typecheck
	cd backend && uv run mypy

lint:
	cd app && npm run lint
	cd backend && uv run ruff check

test:
	cd app && npm test
	cd backend && uv run pytest

imports:             ## separation contracts (app<->sim, sim<->infra)
	cd backend && uv run lint-imports

build:
	cd app && npm run build

up:                  ## start Neo4j + Chroma
	docker compose up -d

down:
	docker compose down

sim:                 ## run the backend simulation harness (built from P2)
	@echo "sim harness lands at P2 (specs/05); placeholder."

fixtures:            ## (re)generate shared /fixtures from the backend (P4+)
	@echo "fixture generation lands at P4 (specs/05); placeholder."
