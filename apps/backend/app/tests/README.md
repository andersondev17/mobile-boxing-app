# Tests Structure

This directory contains all test files organized by type:

## 📁 Directory Structure

```
tests/
├── unit/           # Unit tests for individual functions and classes
├── integration/    # Integration tests for API endpoints and services
├── e2e/           # End-to-end tests for complete workflows
├── conftest.py     # Pytest configuration and fixtures
└── README.md       # This file
```

## 🧪 Test Categories

### Unit Tests (`unit/`)
- Test individual functions in isolation
- Mock external dependencies
- Fast execution, focused testing

**Examples:**
- `test_auth_utils.py` - JWT token creation/verification
- `test_gamification.py` - XP calculation logic
- `test_hybrid_classifier.py` - RF+DTW classification logic

### Integration Tests (`integration/`)
- Test API endpoints with real database
- Test service interactions
- Medium complexity, realistic testing

**Examples:**
- `test_auth_endpoints.py` - Login, register, OAuth flows
- `test_analysis_endpoints.py` - Punch classification API
- `test_gamification_endpoints.py` - XP and achievements API

### End-to-End Tests (`e2e/`)
- Test complete user workflows
- Real infrastructure (Docker, Kafka, etc.)
- Slow execution, comprehensive testing

**Examples:**
- `test_complete_training_session.py` - Full workout flow
- `test_smartwatch_integration.py` - Kafka data pipeline
- `test_ml_pipeline_e2e.py` - Video to classification

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock httpx

# Start required services
docker-compose up -d mongodb postgres redis kafka
```

### Run All Tests
```bash
# From app directory
pytest tests/ -v
```

### Run Specific Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests (requires Docker services)
pytest tests/e2e/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📝 Test Configuration

### Environment Variables for Testing
```bash
ENV_MODE=dev_mock  # Use mocked services for faster tests
LOG_LEVEL=DEBUG     # Detailed logging for debugging
```

### Database Setup
Tests use separate databases:
- PostgreSQL: `boxing_test`
- MongoDB: `boxing_test`
- Redis: `redis://localhost:6380/1`

## 🎯 Test Data

### Fixtures Available
- `test_user` - Sample user for authentication tests
- `test_landmarks` - Sample landmark data for ML tests
- `test_session` - Sample training session data
- `mock_kafka_producer` - Mocked Kafka producer

### Sample Data Files
- `fixtures/sample_landmarks.json` - Test landmark sequences
- `fixtures/baseline_sample.parquet` - Small baseline for testing
- `fixtures/auth_tokens.json` - Sample JWT tokens

## 🔧 Debugging Tests

### Common Issues
1. **Database Connection**: Ensure test databases exist
2. **Kafka Connection**: Mock Kafka for unit/integration tests
3. **Async Tests**: Use `pytest-asyncio` and proper async/await
4. **Time-dependent Tests**: Use freezegun for consistent timestamps

### Debug Commands
```bash
# Run with debugger
pytest tests/unit/test_auth.py --pdb

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

## 📊 Coverage Goals

- **Unit Tests**: 90%+ code coverage
- **Integration Tests**: 80%+ endpoint coverage  
- **E2E Tests**: Cover critical user journeys

## 🔄 CI/CD Integration

Tests run automatically on:
- Pull requests (unit + integration)
- Main branch merges (all tests)
- Releases (full test suite + performance tests)

## 📋 Migration Notes

### From `dev_tests/`
- ML training scripts moved to `tests/unit/ml/`
- Integration scripts moved to `tests/integration/`
- E2E workflows moved to `tests/e2e/`

### Legacy Test Files
- Files in `dev_tests/` have been migrated and organized
- Original files preserved in `tests/legacy/` for reference
