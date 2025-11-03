# Backend Test Suite

This directory contains comprehensive unit tests for the FastAPI backend application.

## Overview

The test suite covers:
- **Routes**: API endpoint testing with FastAPI TestClient
- **Models**: SQLAlchemy model validation and database operations
- **Schemas**: Pydantic schema validation and serialization
- **Config**: Database configuration and connection management

## Setup

### 1. Install Test Dependencies

```bash
cd apps/backend
pip install -r requirements-test.txt
```

### 2. Set Up Environment

Create a `.env` file in `apps/backend/` if not already present:

```env
POSTGRES_DRIVER=postgresql
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=testdb
```

Note: Tests use an in-memory SQLite database by default, so PostgreSQL is not required for testing.

## Running Tests

### Run All Tests

```bash
# From backend directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test Files

```bash
# Test user routes only
pytest tests/routes/test_user.py -v

# Test training routes only
pytest tests/routes/test_training.py -v

# Test all routes
pytest tests/routes/ -v

# Test schemas
pytest tests/schemas/ -v

# Test models
pytest tests/models/ -v
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/routes/test_user.py::TestGetUsers -v

# Run a specific test method
pytest tests/routes/test_user.py::TestGetUsers::test_get_users_empty_database -v
```

### Run Tests with Markers

```bash
# Run tests matching a keyword
pytest -k "user" -v

# Run tests not matching a keyword
pytest -k "not slow" -v
```

## Test Structure