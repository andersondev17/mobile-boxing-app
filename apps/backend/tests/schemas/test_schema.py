"""
Unit tests for Pydantic schemas
Tests data validation, serialization, and edge cases
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.schema import UserBase, TrainingBase, ExerciseBase


class TestUserBase:
    """Tests for UserBase schema."""
    
    def test_valid_user_creation(self):
        """Test creating a valid user."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": datetime.now()
        }
        
        user = UserBase(**user_data)
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
    
    def test_user_missing_required_fields(self):
        """Test user creation with missing fields."""
        with pytest.raises(ValidationError):
            UserBase(id="user123", email="test@example.com")
    
    def test_user_invalid_types(self):
        """Test user creation with invalid types."""
        with pytest.raises(ValidationError):
            UserBase(
                id=123,  # Should be string
                email="test@example.com",
                name="Test",
                role="athlete",
                email_verified=1,
                created_at=datetime.now()
            )
    
    def test_user_from_attributes(self):
        """Test from_attributes configuration."""
        # This tests the Config class setting
        assert UserBase.model_config.get('from_attributes')


class TestTrainingBase:
    """Tests for TrainingBase schema."""
    
    def test_valid_training_creation(self):
        """Test creating a valid training."""
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Morning Workout",
            "status": True,
            "started_at": datetime.now(),
            "ended_at": datetime.now()
        }
        
        training = TrainingBase(**training_data)
        assert training.id == "training123"
        assert training.user_id == "user123"
        assert training.title == "Morning Workout"
        assert training.status is True
    
    def test_training_boolean_status(self):
        """Test that status accepts boolean."""
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Workout",
            "status": False,
            "started_at": datetime.now(),
            "ended_at": datetime.now()
        }
        
        training = TrainingBase(**training_data)
        assert training.status is False
    
    def test_training_invalid_status_type(self):
        """Test that status rejects non-boolean."""
        with pytest.raises(ValidationError):
            TrainingBase(
                id="training123",
                user_id="user123",
                title="Workout",
                status="active",  # Should be boolean
                started_at=datetime.now(),
                ended_at=datetime.now()
            )
    
    def test_training_datetime_validation(self):
        """Test datetime field validation."""
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Workout",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        training = TrainingBase(**training_data)
        assert isinstance(training.started_at, datetime)
        assert isinstance(training.ended_at, datetime)


class TestExerciseBase:
    """Tests for ExerciseBase schema."""
    
    def test_valid_exercise_creation(self):
        """Test creating a valid exercise."""
        exercise_data = {
            "id": "exercise123",
            "title": "Jab Practice",
            "poster_url": "url123",
            "category": "tecnicas_golpeo",
            "difficulty": "beginner",
            "duration_min": "30",
            "description": "Basic jab technique",
            "technique": "Keep guard up",
            "muscles": {"primary": ["shoulders"], "secondary": ["triceps"]},
            "equipment": "gloves"
        }
        
        exercise = ExerciseBase(**exercise_data)
        assert exercise.id == "exercise123"
        assert exercise.title == "Jab Practice"
        assert isinstance(exercise.muscles, dict)
    
    def test_exercise_dict_muscles(self):
        """Test that muscles field accepts dict."""
        exercise_data = {
            "id": "ex1",
            "title": "Exercise",
            "poster_url": "url",
            "category": "cat",
            "difficulty": "easy",
            "duration_min": "10",
            "description": "desc",
            "technique": "tech",
            "muscles": {"test": "value"},
            "equipment": "none"
        }
        
        exercise = ExerciseBase(**exercise_data)
        assert exercise.muscles == {"test": "value"}
    
    def test_exercise_empty_muscles(self):
        """Test exercise with empty muscles dict."""
        exercise_data = {
            "id": "ex1",
            "title": "Exercise",
            "poster_url": "url",
            "category": "cat",
            "difficulty": "easy",
            "duration_min": "10",
            "description": "desc",
            "technique": "tech",
            "muscles": {},
            "equipment": "none"
        }
        
        exercise = ExerciseBase(**exercise_data)
        assert exercise.muscles == {}
    
    def test_exercise_missing_required_fields(self):
        """Test exercise with missing fields."""
        with pytest.raises(ValidationError):
            ExerciseBase(
                id="ex1",
                title="Exercise"
                # Missing other required fields
            )