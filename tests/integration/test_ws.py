"""Integration test for WebSocket route."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_websocket_rejects_without_biometric_consent():
    """Missing or false biometric consent must fail early."""
    with client.websocket_connect("/boxing/ws/jab") as websocket:
        # Mock payload
        websocket.send_json({
            "type": "landmarks",
            "landmarks": [{"x": 0, "y": 0, "z": 0} for _ in range(33)],
            "timestamp": 12345,
            "user_id": "test-no-consent"
        })
        # Need to mock the DB in real setup, but for now it should fail or error
        data = websocket.receive_json()
        assert "error" in data
        assert data["error"] == "consent_required"






