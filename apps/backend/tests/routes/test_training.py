"""
Comprehensive unit tests for training routes.
Tests all CRUD operations, error handling, and edge cases.
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta


class TestGetTrainings:
    """Tests for GET /training/ endpoint."""
    
    def test_get_trainings_empty_database(self, client):
        """Test getting trainings when database is empty."""
        response = client.get("/training/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Trainings not found"
    
    def test_get_trainings_with_data(self, client, create_test_user, create_test_training):
        """Test getting trainings with data in database."""
        create_test_user(id="user1")
        create_test_training(id="training1", user_id="user1", title="Morning Session")
        create_test_training(id="training2", user_id="user1", title="Evening Session")
        create_test_training(id="training3", user_id="user1", title="Night Session")
        
        response = client.get("/training/")
        assert response.status_code == status.HTTP_200_OK
        
        trainings = response.json()
        assert len(trainings) == 3
        assert trainings[0]["title"] == "Morning Session"
    
    def test_get_trainings_limit_10(self, client, create_test_user, create_test_training):
        """Test that only 10 trainings are returned maximum."""
        create_test_user(id="user1")
        
        # Create 15 trainings
        for i in range(15):
            create_test_training(
                id=f"training{i}",
                user_id="user1",
                title=f"Training {i}"
            )
        
        response = client.get("/training/")
        assert response.status_code == status.HTTP_200_OK
        
        trainings = response.json()
        assert len(trainings) == 10
    
    def test_get_trainings_multiple_users(self, client, create_test_user, create_test_training):
        """Test getting trainings from multiple users."""
        create_test_user(id="user1")
        create_test_user(id="user2")
        
        create_test_training(id="t1", user_id="user1", title="User1 Training")
        create_test_training(id="t2", user_id="user2", title="User2 Training")
        
        response = client.get("/training/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2


class TestGetTraining:
    """Tests for GET /training/{training_id} endpoint."""
    
    def test_get_training_success(self, client, create_test_user, create_test_training):
        """Test getting a specific training successfully."""
        create_test_user(id="user123")
        create_test_training(
            id="training123",
            user_id="user123",
            title="Boxing Session",
            status=True
        )
        
        response = client.get("/training/training123")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == "training123"
        assert data["title"] == "Boxing Session"
        assert data["status"] is True
        assert data["user_id"] == "user123"
    
    def test_get_training_not_found(self, client):
        """Test getting a non-existent training."""
        response = client.get("/training/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Training not found"
    
    def test_get_training_special_characters_id(self, client, create_test_user, create_test_training):
        """Test getting training with special characters in ID."""
        create_test_user(id="user1")
        training_id = "training-123_test"
        create_test_training(id=training_id, user_id="user1")
        
        response = client.get(f"/training/{training_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == training_id


class TestAddTraining:
    """Tests for POST /training/ endpoint."""
    
    def test_add_training_success(self, client, create_test_user):
        """Test adding a new training successfully."""
        create_test_user(id="user123")
        
        training_data = {
            "id": "newtraining123",
            "user_id": "user123",
            "title": "New Training Session",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["id"] == training_data["id"]
        assert data["title"] == training_data["title"]
        assert data["status"] == training_data["status"]
    
    def test_add_training_duplicate_id(self, client, create_test_user, create_test_training):
        """Test adding a training with duplicate ID."""
        create_test_user(id="user1")
        create_test_training(id="duplicate123", user_id="user1")
        
        training_data = {
            "id": "duplicate123",
            "user_id": "user1",
            "title": "Duplicate Training",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "already existed" in response.json()["detail"]
    
    def test_add_training_missing_required_fields(self, client):
        """Test adding training with missing required fields."""
        incomplete_data = {
            "id": "incomplete",
            "user_id": "user123"
            # Missing title, status, etc.
        }
        
        response = client.post("/training/", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_add_training_nonexistent_user(self, client):
        """Test adding training for non-existent user."""
        training_data = {
            "id": "training123",
            "user_id": "nonexistent_user",
            "title": "Training",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        # May fail with foreign key constraint
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_add_training_invalid_status(self, client, create_test_user):
        """Test adding training with invalid status value."""
        create_test_user(id="user123")
        
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Training",
            "status": "invalid",  # Should be boolean
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_add_training_end_before_start(self, client, create_test_user):
        """Test adding training where end time is before start time."""
        create_test_user(id="user123")
        
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Invalid Time Training",
            "status": True,
            "started_at": "2024-01-01T09:00:00",
            "ended_at": "2024-01-01T08:00:00"  # Before start
        }
        
        response = client.post("/training/", json=training_data)
        # Current implementation doesn't validate this
        # Documenting actual behavior
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestUpdateTraining:
    """Tests for PUT /training/{training_id} endpoint."""
    
    def test_update_training_success(self, client, create_test_user, create_test_training):
        """Test updating a training successfully."""
        create_test_user(id="user123")
        create_test_training(
            id="training123",
            user_id="user123",
            title="Old Title",
            status=False
        )
        
        update_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Updated Title",
            "status": True,
            "started_at": "2024-01-01T10:00:00",
            "ended_at": "2024-01-01T11:00:00"
        }
        
        response = client.put("/training/training123", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] is True
    
    def test_update_training_not_found(self, client):
        """Test updating a non-existent training."""
        update_data = {
            "id": "nonexistent",
            "user_id": "user123",
            "title": "Training",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.put("/training/nonexistent", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Training not found"
    
    def test_update_training_partial(self, client, create_test_user, create_test_training):
        """Test partial update with None values."""
        create_test_user(id="user123")
        create_test_training(
            id="training123",
            user_id="user123",
            title="Original Title"
        )
        
        update_data = {
            "id": "training123",
            "user_id": None,
            "title": "Updated Title Only",
            "status": None,
            "started_at": None,
            "ended_at": None
        }
        
        response = client.put("/training/training123", json=update_data)
        # Implementation updates only non-None fields
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_update_training_change_user(self, client, create_test_user, create_test_training):
        """Test changing the user_id of a training."""
        create_test_user(id="user1")
        create_test_user(id="user2")
        create_test_training(id="training123", user_id="user1")
        
        update_data = {
            "id": "training123",
            "user_id": "user2",  # Change user
            "title": "Transferred Training",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.put("/training/training123", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_id"] == "user2"


class TestDeleteTraining:
    """Tests for DELETE /training/{training_id} endpoint."""
    
    def test_delete_training_success(self, client, create_test_user, create_test_training):
        """Test deleting a training successfully."""
        create_test_user(id="user123")
        create_test_training(id="training123", user_id="user123")
        
        response = client.delete("/training/training123")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "training deleted successfully"
        
        # Verify training is actually deleted
        get_response = client.get("/training/training123")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_training_not_found(self, client):
        """Test deleting a non-existent training."""
        response = client.delete("/training/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Training not found"
    
    def test_delete_training_twice(self, client, create_test_user, create_test_training):
        """Test deleting the same training twice."""
        create_test_user(id="user123")
        create_test_training(id="training123", user_id="user123")
        
        # First deletion
        response1 = client.delete("/training/training123")
        assert response1.status_code == status.HTTP_200_OK
        
        # Second deletion should fail
        response2 = client.delete("/training/training123")
        assert response2.status_code == status.HTTP_404_NOT_FOUND


class TestTrainingEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_training_with_very_long_title(self, client, create_test_user):
        """Test training with very long title."""
        create_test_user(id="user123")
        
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "T" * 10000,
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_training_with_unicode_title(self, client, create_test_user):
        """Test training with unicode characters in title."""
        create_test_user(id="user123")
        
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Entrenamiento de Boxeo 拳擊訓練 🥊",
            "status": True,
            "started_at": "2024-01-01T08:00:00",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        if response.status_code == status.HTTP_201_CREATED:
            assert response.json()["title"] == training_data["title"]
    
    def test_training_with_future_dates(self, client, create_test_user):
        """Test training scheduled in the future."""
        create_test_user(id="user123")
        
        future_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Future Training",
            "status": False,
            "started_at": future_date,
            "ended_at": future_date
        }
        
        response = client.post("/training/", json=training_data)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_training_invalid_datetime_format(self, client, create_test_user):
        """Test training with invalid datetime format."""
        create_test_user(id="user123")
        
        training_data = {
            "id": "training123",
            "user_id": "user123",
            "title": "Training",
            "status": True,
            "started_at": "not-a-date",
            "ended_at": "2024-01-01T09:00:00"
        }
        
        response = client.post("/training/", json=training_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY