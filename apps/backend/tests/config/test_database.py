"""
Unit tests for database configuration
Tests database setup and connection management
"""
import pytest
from app.config.database import get_db, Base, SessionLocal, engine


class TestDatabaseConfiguration:
    """Tests for database configuration."""
    
    def test_base_declarative_exists(self):
        """Test that Base declarative is defined."""
        assert Base is not None
    
    def test_session_local_exists(self):
        """Test that SessionLocal is defined."""
        assert SessionLocal is not None
    
    def test_engine_exists(self):
        """Test that engine is defined."""
        assert engine is not None
    
    def test_get_db_generator(self):
        """Test that get_db is a generator function."""
        db_gen = get_db()
        assert hasattr(db_gen, '__next__')
    
    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        
        # Cleanup
        try:
            db_gen.close()
        except StopIteration:
            pass
    
    def test_get_db_closes_session(self):
        """Test that get_db properly closes the session."""
        db_gen = get_db()
        db = next(db_gen)
        
        # Consume the generator to trigger finally block
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        # Session should be closed
        assert not db.is_active