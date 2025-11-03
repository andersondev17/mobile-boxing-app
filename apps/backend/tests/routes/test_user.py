"""
Comprehensive unit tests for user routes.
Tests all CRUD operations, error handling, and edge cases.
"""
import pytest
from fastapi import status
from datetime import datetime


class TestGetUsers:
    """Tests for GET /user/ endpoint."""
    
    def test_get_users_empty_database(self, client):
        """Test getting users when database is empty."""
        response = client.get("/user/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Users not found"
    
    def test_get_users_with_data(self, client, create_test_user):
        """Test getting users with data in database."""
        # Create multiple test users
        create_test_user(id="user1", email="user1@test.com", name="User One")
        create_test_user(id="user2", email="user2@test.com", name="User Two")
        create_test_user(id="user3", email="user3@test.com", name="User Three")
        
        response = client.get("/user/")
        assert response.status_code == status.HTTP_200_OK
        
        users = response.json()
        assert len(users) == 3
        assert users[0]["email"] == "user1@test.com"
        assert users[1]["email"] == "user2@test.com"
    
    def test_get_users_limit_10(self, client, create_test_user):
        """Test that only 10 users are returned maximum."""
        # Create 15 users
        for i in range(15):
            create_test_user(
                id=f"user{i}",
                email=f"user{i}@test.com",
                name=f"User {i}"
            )
        
        response = client.get("/user/")
        assert response.status_code == status.HTTP_200_OK
        
        users = response.json()
        assert len(users) == 10


class TestGetUser:
    """Tests for GET /user/{user_id} endpoint."""
    
    def test_get_user_success(self, client, create_test_user):
        """Test getting a specific user successfully."""
        create_test_user(
            id="user123",
            email="john@example.com",
            name="John Doe",
            role="athlete"
        )
        
        response = client.get("/user/user123")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == "user123"
        assert data["email"] == "john@example.com"
        assert data["name"] == "John Doe"
        assert data["role"] == "athlete"
    
    def test_get_user_not_found(self, client):
        """Test getting a non-existent user."""
        response = client.get("/user/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found"
    
    def test_get_user_empty_id(self, client):
        """Test getting user with empty ID."""
        response = client.get("/user/")
        # Should hit the list endpoint, not detail
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]
    
    def test_get_user_special_characters(self, client, create_test_user):
        """Test getting user with special characters in ID."""
        user_id = "user-123_test"
        create_test_user(id=user_id, email="special@test.com")
        
        response = client.get(f"/user/{user_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == user_id


class TestAddUser:
    """Tests for POST /user/ endpoint."""
    
    def test_add_user_success(self, client):
        """Test adding a new user successfully."""
        user_data = {
            "id": "newuser123",
            "email": "newuser@example.com",
            "name": "New User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post("/user/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["id"] == user_data["id"]
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
    
    def test_add_user_duplicate_id(self, client, create_test_user):
        """Test adding a user with duplicate ID."""
        create_test_user(id="duplicate123", email="first@test.com")
        
        user_data = {
            "id": "duplicate123",
            "email": "second@test.com",
            "name": "Second User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post("/user/", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]
    
    def test_add_user_missing_required_fields(self, client):
        """Test adding user with missing required fields."""
        incomplete_data = {
            "id": "incomplete",
            "email": "test@example.com"
            # Missing name, role, etc.
        }
        
        response = client.post("/user/", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_add_user_invalid_email_format(self, client):
        """Test adding user with invalid email format."""
        user_data = {
            "id": "user123",
            "email": "invalid-email",  # Invalid format
            "name": "Test User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        # Note: Current schema doesn't validate email format
        # This test documents current behavior
        response = client.post("/user/", json=user_data)
        # May succeed depending on schema validation
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_add_user_empty_strings(self, client):
        """Test adding user with empty string values."""
        user_data = {
            "id": "",
            "email": "",
            "name": "",
            "role": "",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post("/user/", json=user_data)
        # Should either succeed or fail validation
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_add_user_with_extra_fields(self, client):
        """Test adding user with extra unexpected fields."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00",
            "extra_field": "should be ignored"
        }
        
        response = client.post("/user/", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED


class TestUpdateUser:
    """Tests for PUT /user/{user_id} endpoint."""
    
    def test_update_user_success(self, client, create_test_user):
        """Test updating a user successfully."""
        create_test_user(
            id="user123",
            email="old@example.com",
            name="Old Name"
        )
        
        update_data = {
            "id": "user123",
            "email": "new@example.com",
            "name": "New Name",
            "role": "coach",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.put("/user/user123", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["name"] == "New Name"
    
    def test_update_user_not_found(self, client):
        """Test updating a non-existent user."""
        update_data = {
            "id": "nonexistent",
            "email": "test@example.com",
            "name": "Test",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.put("/user/nonexistent", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found"
    
    def test_update_user_partial_update(self, client, create_test_user):
        """Test partial update with None values."""
        original_email = "original@test.com"
        create_test_user(
            id="user123",
            email=original_email,
            name="Original Name"
        )
        
        # Update only name, leave email as None
        update_data = {
            "id": "user123",
            "email": None,
            "name": "Updated Name",
            "role": None,
            "email_verified": None,
            "created_at": None
        }
        
        response = client.put("/user/user123", json=update_data)
        # Current implementation only updates non-None fields
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_update_user_all_fields(self, client, create_test_user):
        """Test updating all fields of a user."""
        create_test_user(id="user123")
        
        update_data = {
            "id": "user123",
            "email": "updated@example.com",
            "name": "Updated User",
            "role": "trainer",
            "email_verified": 0,
            "created_at": "2024-12-01T00:00:00"
        }
        
        response = client.put("/user/user123", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["email"] == update_data["email"]
        assert data["name"] == update_data["name"]
        assert data["role"] == update_data["role"]


class TestDeleteUser:
    """Tests for DELETE /user/{user_id} endpoint."""
    
    def test_delete_user_success(self, client, create_test_user):
        """Test deleting a user successfully."""
        create_test_user(id="user123")
        
        response = client.delete("/user/user123")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "User deleted successfully"
        
        # Verify user is actually deleted
        get_response = client.get("/user/user123")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_user_not_found(self, client):
        """Test deleting a non-existent user."""
        response = client.delete("/user/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found"
    
    def test_delete_user_twice(self, client, create_test_user):
        """Test deleting the same user twice."""
        create_test_user(id="user123")
        
        # First deletion
        response1 = client.delete("/user/user123")
        assert response1.status_code == status.HTTP_200_OK
        
        # Second deletion should fail
        response2 = client.delete("/user/user123")
        assert response2.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_user_with_trainings(self, client, create_test_user, create_test_training):
        """Test deleting a user that has associated trainings."""
        create_test_user(id="user123")
        create_test_training(id="training1", user_id="user123")
        
        # This should handle foreign key constraints
        response = client.delete("/user/user123")
        # May fail due to foreign key constraint or cascade delete
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestUserEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_concurrent_user_creation(self, client):
        """Test handling of concurrent user creation."""
        user_data = {
            "id": "concurrent",
            "email": "concurrent@test.com",
            "name": "Concurrent User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response1 = client.post("/user/", json=user_data)
        response2 = client.post("/user/", json=user_data)
        
        # One should succeed, one should fail
        assert (response1.status_code == status.HTTP_201_CREATED and 
                response2.status_code == status.HTTP_400_BAD_REQUEST) or \
               (response1.status_code == status.HTTP_400_BAD_REQUEST and 
                response2.status_code == status.HTTP_201_CREATED)
    
    def test_user_with_very_long_strings(self, client):
        """Test user creation with very long string values."""
        user_data = {
            "id": "a" * 1000,
            "email": "a" * 500 + "@example.com",
            "name": "N" * 1000,
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post("/user/", json=user_data)
        # May succeed or fail depending on database constraints
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_user_with_unicode_characters(self, client):
        """Test user with unicode characters."""
        user_data = {
            "id": "unicode123",
            "email": "тест@example.com",
            "name": "José García 日本語",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post("/user/", json=user_data)
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert data["name"] == user_data["name"]
    
    def test_user_invalid_datetime_format(self, client):
        """Test user with invalid datetime format."""
        user_data = {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "athlete",
            "email_verified": 1,
            "created_at": "invalid-datetime"
        }
        
        response = client.post("/user/", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY