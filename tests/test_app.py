"""
Tests for the High School Management System API
"""

import pytest
from fastapi import HTTPException


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that all activities are returned"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all activities are returned
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 9

    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_participants_is_list(self, client, reset_activities):
        """Test that participants is a list"""
        response = client.get("/activities")
        data = response.json()
        
        assert isinstance(data["Chess Club"]["participants"], list)


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client, reset_activities):
        """Test successful signup for a new student"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "alex@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup adds the participant to the activity"""
        email = "alex@mergington.edu"
        
        # Signup
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        
        # Verify by fetching activities
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Team"]["participants"]

    def test_signup_duplicate_email_fails(self, client, reset_activities):
        """Test that signing up with the same email twice fails"""
        email = "test@mergington.edu"
        activity = "Basketball Team"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_existing_participant_fails(self, client, reset_activities):
        """Test that an already registered participant can't signup again"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Fake Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Test that multiple different students can sign up for the same activity"""
        activity = "Basketball Team"
        
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestRemove:
    """Tests for the DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant"""
        email = "michael@mergington.edu"
        
        response = client.delete(
            "/activities/Chess Club/remove",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_remove_removes_participant_from_activity(self, client, reset_activities):
        """Test that remove actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Verify participant is registered
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Remove participant
        client.delete(
            "/activities/Chess Club/remove",
            params={"email": email}
        )
        
        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing a non-registered participant fails"""
        response = client.delete(
            "/activities/Basketball Team/remove",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing from a non-existent activity fails"""
        response = client.delete(
            "/activities/Fake Activity/remove",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_last_participant(self, client, reset_activities):
        """Test removing the last participant from an activity"""
        activity = "Basketball Team"
        email = "test@mergington.edu"
        
        # Signup
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Remove
        response = client.delete(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify activity now has no participants
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == 0


class TestIntegration:
    """Integration tests combining multiple endpoints"""

    def test_signup_and_remove_workflow(self, client, reset_activities):
        """Test a complete workflow of signup and removal"""
        email = "workflow@mergington.edu"
        activity = "Tennis Club"
        
        # 1. Verify activity exists and is empty
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == 0
        
        # 2. Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # 3. Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # 4. Remove
        response = client.delete(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # 5. Verify removal
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_signups_and_removals(self, client, reset_activities):
        """Test multiple signups and removals"""
        activity = "Drama Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up all
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # Remove middle one
        response = client.delete(
            f"/activities/{activity}/remove",
            params={"email": emails[1]}
        )
        assert response.status_code == 200
        
        # Verify state
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert emails[0] in participants
        assert emails[1] not in participants
        assert emails[2] in participants
