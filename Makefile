.PHONY: run-dev migrate migrate-make migrate-rollback help

# Default target
help:
	@echo "Available commands:"
	@echo "  make run-dev              - Run FastAPI app with auto-reload"
	@echo "  make migrate              - Run all pending migrations"
	@echo "  make migrate-make MESSAGE=\"message\" - Create a new migration (autogenerate)"
	@echo "  make migrate-rollback     - Rollback the last migration"

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
