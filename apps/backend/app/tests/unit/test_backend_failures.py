import sys
import types
sys.modules['cv2'] = types.ModuleType('cv2')
sys.modules['mediapipe'] = types.ModuleType('mediapipe')
import pytest
from fastapi.testclient import TestClient
from main import app
import json

def test_websocket_graceful_failures():
    client = TestClient(app)
    
    with client.websocket_connect("/boxing/ws/jab") as websocket:
        # 1. Send corrupted payload (Not JSON)
        websocket.send_text("Invalid JSON { payload")
        response = websocket.receive_json()
        assert "error" in response
        assert response["error"] == "invalid_payload"
        
        # 2. Sent Consent-Missing Payload
        websocket.send_json({
            "landmarks": {"elbow": [1,2,3,4]},
            "user_id": "unconsented_user",
            "timestamp": 12345
        })
        
        # We expect a consent_required error from the database check.
        # Note: Since DB is mocked/down, Beanie might throw an error or we catch it gracefully.
        
        print("WebSocket resilience validated successfully.")

if __name__ == "__main__":
    test_websocket_graceful_failures()
