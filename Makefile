.PHONY: install install-dev format lint typecheck test run-api up down

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

up:
	docker compose up -d

down:
	docker compose down
