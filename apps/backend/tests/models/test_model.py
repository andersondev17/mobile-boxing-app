"""
Unit tests for SQLAlchemy models
Tests model structure, relationships, and constraints
"""
import pytest
from datetime import datetime
from app.models.model import User, Role, Training, Exercise, PosterUrl, Category, Difficulty


class TestUserModel:
    """Tests for User model."""
    
    def test_user_table_name(self):
        """Test that table name is correct."""
        assert User.__tablename__ == "user"
    
    def test_user_columns_exist(self):
        """Test that all columns are defined."""
        columns = User.__table__.columns.keys()
        assert 'id' in columns
        assert 'email' in columns
        assert 'name' in columns
        assert 'role' in columns
        assert 'email_verified' in columns
        assert 'created_at' in columns
    
    def test_user_primary_key(self):
        """Test that id is primary key."""
        assert User.__table__.primary_key.columns.keys() == ['id']
    
    def test_user_creation(self, test_db):
        """Test creating a user instance."""
        user = User(
            id="user123",
            email="test@example.com",
            name="Test User",
            role="athlete",
            email_verified=True,
            created_at=datetime.utcnow()
        )
        
        test_db.add(user)
        test_db.commit()
        
        retrieved = test_db.query(User).filter_by(id="user123").first()
        assert retrieved is not None
        assert retrieved.email == "test@example.com"


class TestTrainingModel:
    """Tests for Training model."""
    
    def test_training_table_name(self):
        """Test that table name is correct."""
        assert Training.__tablename__ == "training"
    
    def test_training_columns_exist(self):
        """Test that all columns are defined."""
        columns = Training.__table__.columns.keys()
        assert 'id' in columns
        assert 'user_id' in columns
        assert 'title' in columns
        assert 'status' in columns
        assert 'started_at' in columns
        assert 'ended_at' in columns
    
    def test_training_foreign_key(self):
        """Test that user_id has foreign key."""
        foreign_keys = [fk.column.name for fk in Training.__table__.foreign_keys]
        assert 'id' in foreign_keys  # References user.id
    
    def test_training_creation(self, test_db, create_test_user):
        """Test creating a training instance."""
        create_test_user(id="user123")
        
        training = Training(
            id="training123",
            user_id="user123",
            title="Morning Session",
            status=True,
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow()
        )
        
        test_db.add(training)
        test_db.commit()
        
        retrieved = test_db.query(Training).filter_by(id="training123").first()
        assert retrieved is not None
        assert retrieved.title == "Morning Session"


class TestExerciseModel:
    """Tests for Exercise model."""
    
    def test_exercise_table_name(self):
        """Test that table name is correct."""
        assert Exercise.__tablename__ == "exercise"
    
    def test_exercise_columns_exist(self):
        """Test that all columns are defined."""
        columns = Exercise.__table__.columns.keys()
        assert 'id' in columns
        assert 'title' in columns
        assert 'poster_url' in columns
        assert 'category' in columns
        assert 'difficulty' in columns
        assert 'duration_min' in columns
        assert 'description' in columns
        assert 'technique' in columns
        assert 'muscles' in columns
        assert 'equipment' in columns
    
    def test_exercise_muscles_json_type(self):
        """Test that muscles column is JSON type."""
        muscles_col = Exercise.__table__.columns['muscles']
        assert str(muscles_col.type) == 'JSON'


class TestRoleModel:
    """Tests for Role model."""
    
    def test_role_table_name(self):
        """Test that table name is correct."""
        assert Role.__tablename__ == "role"
    
    def test_role_columns_exist(self):
        """Test that all columns are defined."""
        columns = Role.__table__.columns.keys()
        assert 'id' in columns
        assert 'description' in columns


class TestPosterUrlModel:
    """Tests for PosterUrl model."""
    
    def test_poster_url_table_name(self):
        """Test that table name is correct."""
        assert PosterUrl.__tablename__ == "poster_url"
    
    def test_poster_url_columns_exist(self):
        """Test that all columns are defined."""
        columns = PosterUrl.__table__.columns.keys()
        assert 'id' in columns
        assert 'url' in columns


class TestCategoryModel:
    """Tests for Category model."""
    
    def test_category_table_name(self):
        """Test that table name is correct."""
        assert Category.__tablename__ == "category"
    
    def test_category_columns_exist(self):
        """Test that all columns are defined."""
        columns = Category.__table__.columns.keys()
        assert 'id' in columns
        assert 'description' in columns


class TestDifficultyModel:
    """Tests for Difficulty model."""
    
    def test_difficulty_table_name(self):
        """Test that table name is correct."""
        assert Difficulty.__tablename__ == "difficulty"
    
    def test_difficulty_columns_exist(self):
        """Test that all columns are defined."""
        columns = Difficulty.__table__.columns.keys()
        assert 'id' in columns
        assert 'description' in columns