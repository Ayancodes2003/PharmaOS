.PHONY: install install-dev format lint typecheck test run-api run-api-prod up up-deps down down-v smoke smoke-api

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

format:
	ruff check --fix src tests

lint:
	ruff check src tests

typecheck:
	mypy src

test:
	pytest

run-api:
	uvicorn pharma_os.main:app --host 0.0.0.0 --port 8000 --reload

run-api-prod:
	uvicorn pharma_os.main:app --host 0.0.0.0 --port 8000

up:
	docker compose up -d

up-deps:
	docker compose up -d postgres mongo

down:
	docker compose down

down-v:
	docker compose down -v

smoke:
	python scripts/run_runtime_smoke.py

smoke-api:
	python scripts/run_runtime_smoke.py --check-api
