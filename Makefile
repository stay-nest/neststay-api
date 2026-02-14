.PHONY: run-dev migrate migrate-make migrate-rollback seed seed-hotels seed-locations seed-room-types seed-guests lint lint-fix format format-check check test test-cov test-watch help

# Default target
help:
	@echo "Available commands:"
	@echo "  make run-dev              - Run FastAPI app with auto-reload"
	@echo "  make migrate              - Run all pending migrations"
	@echo "  make migrate-make MESSAGE=\"message\" - Create a new migration (autogenerate)"
	@echo "  make migrate-rollback     - Rollback the last migration"
	@echo "  make seed                 - Seed all tables"
	@echo "  make seed-hotels          - Seed hotels only"
	@echo "  make seed-locations      - Seed locations only"
	@echo "  make seed-room-types     - Seed room types only"
	@echo "  make seed-guests          - Seed guests only"
	@echo "  make lint                 - Check for linting issues"
	@echo "  make lint-fix             - Auto-fix linting issues"
	@echo "  make format               - Format all files"
	@echo "  make format-check         - Check formatting without changes"
	@echo "  make check                - Run all checks (for CI)"
	@echo "  make test                 - Run all tests"
	@echo "  make test-cov             - Run tests with coverage report"
	@echo "  make test-watch           - Run tests in watch mode (requires pytest-watch)"

# Run FastAPI app with reload enabled
run-dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
migrate:
	uv run alembic -c database/alembic.ini upgrade head

# Create a new migration with autogenerate
migrate-make:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Error: MESSAGE is required. Usage: make migrate-make MESSAGE=\"your message here\""; \
		exit 1; \
	fi
	uv run alembic -c database/alembic.ini revision --autogenerate -m "$(MESSAGE)"

# Rollback last migration
migrate-rollback:
	uv run alembic -c database/alembic.ini downgrade -1

# Seed database (default 10 records per table; use -c N with run for custom count)
seed:
	uv run python -m database.seeders.run all

seed-hotels:
	uv run python -m database.seeders.run hotel

seed-locations:
	uv run python -m database.seeders.run location

seed-room-types:
	uv run python -m database.seeders.run room_type

seed-guests:
	uv run python -m database.seeders.run guest

# Linting and formatting
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# Combined check (for CI)
check:
	uv run ruff format --check .
	uv run ruff check .

# Testing
test:
	uv run --group test pytest

test-cov:
	uv run --group test pytest --cov=app --cov-report=term-missing --cov-report=html

test-watch:
	uv run --group test pytest --watch
