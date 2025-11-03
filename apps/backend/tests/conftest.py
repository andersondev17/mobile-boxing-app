"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.main import app
from app.models.model import User, Role, Training, Exercise, PosterUrl, Category, Difficulty


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    # Use in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal()
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user123",
        "email": "test@example.com",
        "name": "Test User",
        "role": "athlete",
        "email_verified": 1,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_training_data():
    """Sample training data for testing."""
    return {
        "id": "training123",
        "user_id": "user123",
        "title": "Morning Workout",
        "status": True,
        "started_at": "2024-01-01T08:00:00",
        "ended_at": "2024-01-01T09:00:00"
    }


@pytest.fixture
def create_test_user(test_db):
    """Factory fixture to create test users."""
    def _create_user(**kwargs):
        from datetime import datetime
        
        user_data = {
            "id": "test_user",
            "email": "test@example.com",
            "name": "Test User",
            "role": "athlete",
            "email_verified": True,
            "created_at": datetime.utcnow()
        }
        user_data.update(kwargs)
        
        user = User(**user_data)
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def create_test_training(test_db):
    """Factory fixture to create test trainings."""
    def _create_training(**kwargs):
        from datetime import datetime
        
        training_data = {
            "id": "test_training",
            "user_id": "test_user",
            "title": "Test Training",
            "status": True,
            "started_at": datetime.utcnow(),
            "ended_at": datetime.utcnow()
        }
        training_data.update(kwargs)
        
        training = Training(**training_data)
        test_db.add(training)
        test_db.commit()
        test_db.refresh(training)
        return training
    
    return _create_training