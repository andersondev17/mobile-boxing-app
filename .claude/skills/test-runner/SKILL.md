---
name: test-runner
description: Apply this skill when running tests for the boxing app backend or mobile, interpreting test output, or fixing test failures. Contains the exact pytest and jest commands for this project. Trigger on: "run tests", "execute tests", "pytest", "jest", "test fails", "run test suite", "check tests", "test coverage", "make tests pass".
---

# Test Runner — mobile-boxing-app

## Backend tests (pytest)

### Prerequisites
```bash
# Services needed for integration tests
docker-compose up mongodb redis -d

# Install test dependencies (if not in requirements.txt)
pip install pytest pytest-asyncio httpx coverage
```

### Run commands
```bash
# Navigate to backend
cd apps/backend/app

# All tests
pytest tests/ -v

# Specific module
pytest tests/test_ml_service/ -v
pytest tests/test_routes/test_boxing.py -v

# With coverage report
pytest tests/ --cov=. --cov-report=term-missing --cov-omit="tests/*"

# Fast tests only (skip integration markers)
pytest tests/ -m "not integration" -v

# Stop on first failure
pytest tests/ -x -v

# Verbose with full output (no truncation)
pytest tests/ -v -s
```

### Test markers
```python
# In tests:
@pytest.mark.integration  # requires running Docker services
@pytest.mark.slow         # long-running tests

# Run without integration tests:
pytest -m "not integration"
```

### Expected output (healthy)
```
tests/test_ml_service/test_feature_extractor.py::test_extract_features_extended_jab PASSED
tests/test_ml_service/test_feature_extractor.py::test_extract_features_too_few_landmarks PASSED
tests/test_ml_service/test_feedback_engine.py::test_feedback_good_technique PASSED
...
5 passed in 0.43s
```

### Common failures and fixes

**`ModuleNotFoundError: No module named 'schemas'`**
```bash
# Run from apps/backend/app/ not from root
cd apps/backend/app && pytest tests/
```

**`ConnectionRefusedError` in integration tests**
```bash
# Start required services first
docker-compose up mongodb redis -d
```

**`RuntimeWarning: coroutine was never awaited`**
```python
# Add to conftest.py
import pytest
pytest_plugins = ('pytest_asyncio',)
```

**Beanie not initialized**
```python
# conftest.py
@pytest.fixture(autouse=True)
async def init_beanie():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.test_db, document_models=[User, Consent])
    yield
    client.close()
```

---

## Mobile tests (Jest)

### Run commands
```bash
# Navigate to mobile
cd apps/mobile

# All tests
npx jest --watchAll=false

# Specific file
npx jest hooks/useSavedExercises.test.ts

# With coverage
npx jest --coverage --watchAll=false

# Watch mode (during development)
npx jest --watch
```

### Expected output (healthy)
```
PASS  hooks/useSavedExercises.test.ts
  ✓ toggleSave adds exercise to saved list (12ms)
  ✓ toggleSave removes already-saved exercise (8ms)
  ✓ isExerciseSaved returns true for saved exercise (5ms)

Test Suites: 1 passed, 1 total
Tests:       3 passed, 3 total
```

---

## CI-equivalent local check (run before PR)

```bash
# Backend
cd apps/backend/app
pytest tests/ --cov=. --cov-report=term-missing --cov-fail-under=75

# Mobile
cd apps/mobile
npx jest --watchAll=false --passWithNoTests

# Lint
cd apps/backend/app && python -m black --check .
cd apps/mobile && npx tsc --noEmit
```

All 4 commands must pass before opening a PR.


