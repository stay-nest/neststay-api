# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NestStay API is a FastAPI backend for a property/hotel management application, using SQLModel as the ORM with MySQL database and Alembic for migrations.

## Commands

```bash
# Run development server (with auto-reload)
make run-dev

# Run database migrations
make migrate

# Create new migration
make migrate-make MESSAGE="your migration message"

# Rollback last migration
make migrate-rollback

# Run tests
make test

# Run tests with coverage report
make test-cov
```

## Architecture

- **main.py** - FastAPI application entry point
- **config.py** - Environment configuration via `Settings` class (loads from `.env`)
- **database/** - Database layer
  - `database.py` - SQLModel engine and session management
  - `alembic/` - Migration scripts (models must be imported in `env.py` for autogenerate)
- **app/** - Application code
  - `models/` - SQLModel entity definitions (e.g., `Hotel`)
  - `schemas/` - Pydantic models for request/response validation
  - `repositories/` - Single-table database operations
  - `services/` - Business logic coordinating multiple repositories
  - `routes/` - FastAPI endpoints

## Key Patterns

- Uses `uv` as the package manager
- Models use SQLModel (combines SQLAlchemy + Pydantic)
- New models must be imported in `database/alembic/env.py` for migration autogeneration
- Database session is injected via FastAPI's `Depends(get_session)`

## Repository and Service Layer Rules

- **Repositories**: Handle single-table operations only. Never call other repositories. Never commit transactions.
- **Services**: Coordinate multiple repositories when an operation spans tables. Own the transaction (`commit()`).
- **Routes**: Stay thin - delegate to services or repositories.

Use a service when:
- Operation affects multiple tables
- Complex business logic is needed

Use repository directly in route when:
- Simple CRUD on a single table

See `docs/architecture.md` for detailed examples.

## Testing

- Uses pytest with SQLite in-memory database
- Test client overrides the database session dependency
- Tests are organized in `tests/` directory:
  - `tests/conftest.py` - Shared fixtures (session, client, sample data)
  - `tests/api/` - API endpoint tests
- All models must be imported in `tests/conftest.py` for table creation

**IMPORTANT**: Run `make test` after every implementation to ensure no existing functionality is broken. Do not consider a task complete until all tests pass.
