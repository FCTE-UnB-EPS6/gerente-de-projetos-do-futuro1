.PHONY: install test lint format typecheck audit run check

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy

audit:
	pip-audit

run:
	uvicorn gpf.api.main:app --reload --host 0.0.0.0 --port 8000

check: lint typecheck test
