import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app


class TestApp:
    """Test suite for basic app functionality"""
    
    def test_root_redirect(self):
        """Test that root path redirects to static/index.html"""
        client = TestClient(app)
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
    
    def test_get_activities(self):
        """Test getting all activities"""
        client = TestClient(app)
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that we have some activities
        assert len(data) > 0
        
        # Check structure of activities
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestActivitySignup:
    """Test suite for activity signup functionality"""
    
    def setup_method(self):
        """Reset activities before each test"""
        from app import activities
        activities.clear()
        activities.update({
            "Test Activity": {
                "description": "A test activity",
                "schedule": "Test schedule",
                "max_participants": 2,
                "participants": ["existing@mergington.edu"]
            },
            "Full Activity": {
                "description": "A full test activity",
                "schedule": "Test schedule",
                "max_participants": 1,
                "participants": ["full@mergington.edu"]
            }
        })
        self.client = TestClient(app)
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = self.client.post(
            "/activities/Test Activity/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Test Activity" in data["message"]
        
        # Verify the participant was added
        activities_response = self.client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Test Activity"]["participants"]
    
    def test_signup_nonexistent_activity(self):
        """Test signup for a non-existent activity"""
        response = self.client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self):
        """Test signup when student is already registered"""
        response = self.client.post(
            "/activities/Test Activity/signup?email=existing@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student is already signed up"
    
    def test_signup_missing_email(self):
        """Test signup without providing email parameter"""
        response = self.client.post("/activities/Test Activity/signup")
        assert response.status_code == 422  # FastAPI validation error


class TestActivityUnregister:
    """Test suite for activity unregistration functionality"""
    
    def setup_method(self):
        """Reset activities before each test"""
        from app import activities
        activities.clear()
        activities.update({
            "Test Activity": {
                "description": "A test activity",
                "schedule": "Test schedule",
                "max_participants": 3,
                "participants": ["student1@mergington.edu", "student2@mergington.edu"]
            },
            "Empty Activity": {
                "description": "An empty test activity",
                "schedule": "Test schedule",
                "max_participants": 2,
                "participants": []
            }
        })
        self.client = TestClient(app)
    
    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        response = self.client.delete(
            "/activities/Test Activity/unregister?email=student1@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "student1@mergington.edu" in data["message"]
        assert "Test Activity" in data["message"]
        
        # Verify the participant was removed
        activities_response = self.client.get("/activities")
        activities_data = activities_response.json()
        assert "student1@mergington.edu" not in activities_data["Test Activity"]["participants"]
        assert "student2@mergington.edu" in activities_data["Test Activity"]["participants"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregistration from a non-existent activity"""
        response = self.client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_registered(self):
        """Test unregistration when student is not registered"""
        response = self.client.delete(
            "/activities/Empty Activity/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"
    
    def test_unregister_missing_email(self):
        """Test unregistration without providing email parameter"""
        response = self.client.delete("/activities/Test Activity/unregister")
        assert response.status_code == 422  # FastAPI validation error


class TestDataIntegrity:
    """Test suite for data consistency and edge cases"""
    
    def setup_method(self):
        """Reset activities before each test"""
        from app import activities
        activities.clear()
        activities.update({
            "Math Club": {
                "description": "Mathematics activities",
                "schedule": "Mondays 3-4 PM",
                "max_participants": 2,
                "participants": ["alice@mergington.edu"]
            }
        })
        self.client = TestClient(app)
    
    def test_activity_capacity_enforcement(self):
        """Test that activities don't exceed their maximum capacity"""
        # Fill the activity to capacity
        response1 = self.client.post(
            "/activities/Math Club/signup?email=bob@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Verify activity is at capacity
        activities_response = self.client.get("/activities")
        activities_data = activities_response.json()
        math_club = activities_data["Math Club"]
        assert len(math_club["participants"]) == math_club["max_participants"]
    
    def test_signup_and_unregister_workflow(self):
        """Test complete workflow: signup then unregister"""
        email = "workflow@mergington.edu"
        activity = "Math Club"
        
        # Sign up
        signup_response = self.client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = self.client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister
        unregister_response = self.client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = self.client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]
    
    def test_special_characters_in_email(self):
        """Test handling of special characters in email addresses"""
        special_email = "test.email-tag@mergington.edu"
        
        response = self.client.post(
            f"/activities/Math Club/signup?email={special_email}"
        )
        assert response.status_code == 200
        
        # Verify the participant was added correctly
        activities_response = self.client.get("/activities")
        activities_data = activities_response.json()
        assert special_email in activities_data["Math Club"]["participants"]