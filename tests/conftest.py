import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def sample_activities():
    """Fixture to reset activities to a known state for testing"""
    from app import activities
    
    # Store original activities
    original_activities = activities.copy()
    
    # Reset to a known test state
    activities.clear()
    activities.update({
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Test schedule",
            "max_participants": 2,
            "participants": ["test1@mergington.edu"]
        },
        "Empty Activity": {
            "description": "An empty test activity",
            "schedule": "Test schedule",
            "max_participants": 1,
            "participants": []
        }
    })
    
    yield activities
    
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)