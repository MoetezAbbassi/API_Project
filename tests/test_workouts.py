"""
Workout endpoint tests.
"""

import pytest
from app.models import Workout, Exercise


class TestWorkoutCreate:
    """Test workout creation endpoint."""
    
    def test_create_workout_success(self, test_client, auth_headers, sample_user):
        """Test successful workout creation."""
        response = test_client.post(
            '/api/workouts',
            headers=auth_headers,
            json={
                "workout_type": "strength",
                "notes": "Upper body workout"
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['status'] == "in_progress"
        assert 'workout_id' in data['data']
    
    def test_create_workout_invalid_type(self, test_client, auth_headers):
        """Test creating workout with invalid type."""
        response = test_client.post(
            '/api/workouts',
            headers=auth_headers,
            json={
                "workout_type": "invalid_type",
                "notes": "Test"
            }
        )
        
        assert response.status_code == 400
    
    def test_create_workout_unauthorized(self, test_client):
        """Test creating workout without authentication."""
        response = test_client.post(
            '/api/workouts',
            json={
                "workout_type": "strength",
                "notes": "Test"
            }
        )
        
        assert response.status_code == 401


class TestWorkoutAddExercise:
    """Test adding exercises to workouts."""
    
    def test_add_exercise_success(self, test_app, test_client, auth_headers, sample_user):
        """Test successfully adding exercise to workout."""
        with test_app.app_context():
            # Create a workout first
            workout_response = test_client.post(
                '/api/workouts',
                headers=auth_headers,
                json={"workout_type": "strength"}
            )
            workout_id = workout_response.get_json()['data']['workout_id']
            
            # Get an exercise (or create one)
            exercise = Exercise.query.first()
            if not exercise:
                pytest.skip("No exercises available in test database")
            
            # Add exercise to workout
            response = test_client.post(
                f'/api/workouts/{workout_id}/exercises',
                headers=auth_headers,
                json={
                    "exercise_id": exercise.exercise_id,
                    "sets": 3,
                    "reps": 10,
                    "weight_used": 185,
                    "weight_unit": "lbs"
                }
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert 'calories_burned' in data['data']


class TestWorkoutComplete:
    """Test completing workouts."""
    
    def test_complete_workout_success(self, test_app, test_client, auth_headers, sample_user):
        """Test successfully completing a workout."""
        with test_app.app_context():
            # Create a workout
            workout_response = test_client.post(
                '/api/workouts',
                headers=auth_headers,
                json={"workout_type": "strength"}
            )
            workout_id = workout_response.get_json()['data']['workout_id']
            
            # Complete the workout
            response = test_client.put(
                f'/api/workouts/{workout_id}',
                headers=auth_headers,
                json={
                    "status": "completed",
                    "notes": "Great workout!"
                }
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['data']['status'] == "completed"
            assert 'completed_at' in data['data']


class TestWorkoutDetail:
    """Test getting workout details."""
    
    def test_get_workout_detail_success(self, test_app, test_client, auth_headers, sample_user):
        """Test getting workout details."""
        with test_app.app_context():
            # Create a workout
            workout_response = test_client.post(
                '/api/workouts',
                headers=auth_headers,
                json={"workout_type": "strength"}
            )
            workout_id = workout_response.get_json()['data']['workout_id']
            
            # Get workout detail
            response = test_client.get(
                f'/api/workouts/{workout_id}',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['data']['workout_id'] == workout_id
            assert 'workout_exercises' in data['data']
    
    def test_get_workout_not_found(self, test_client, auth_headers):
        """Test getting nonexistent workout."""
        response = test_client.get(
            '/api/workouts/nonexistent_id',
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestWorkoutList:
    """Test listing workouts."""
    
    def test_get_user_workouts_success(self, test_app, test_client, auth_headers, sample_user):
        """Test getting user's workouts with pagination."""
        with test_app.app_context():
            user_id = sample_user.user_id
            
            # Create a few workouts
            for i in range(3):
                test_client.post(
                    '/api/workouts',
                    headers=auth_headers,
                    json={"workout_type": "strength", "notes": f"Workout {i+1}"}
                )
            
            # Get workouts
            response = test_client.get(
                f'/api/workouts/{user_id}?page=1&per_page=10',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'total' in data
            assert 'page' in data
            assert len(data['data']) > 0


class TestWorkoutDelete:
    """Test deleting workouts."""
    
    def test_delete_workout_success(self, test_app, test_client, auth_headers, sample_user):
        """Test successfully deleting a workout."""
        with test_app.app_context():
            # Create a workout
            workout_response = test_client.post(
                '/api/workouts',
                headers=auth_headers,
                json={"workout_type": "strength"}
            )
            workout_id = workout_response.get_json()['data']['workout_id']
            
            # Delete the workout
            response = test_client.delete(
                f'/api/workouts/{workout_id}',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


class TestCaloriesCalculation:
    """Test calorie calculations."""
    
    def test_calories_calculation_correct(self, test_app, test_client, auth_headers, sample_user):
        """Test that calories are calculated correctly when adding exercises."""
        with test_app.app_context():
            # Create a workout
            workout_response = test_client.post(
                '/api/workouts',
                headers=auth_headers,
                json={"workout_type": "strength"}
            )
            workout_id = workout_response.get_json()['data']['workout_id']
            
            # Get an exercise
            exercise = Exercise.query.first()
            if not exercise:
                pytest.skip("No exercises available in test database")
            
            # Calculate expected calories
            sets = 3
            reps = 10
            expected_calories = sets * reps * exercise.typical_calories_per_minute / 10
            
            # Add exercise to workout
            response = test_client.post(
                f'/api/workouts/{workout_id}/exercises',
                headers=auth_headers,
                json={
                    "exercise_id": exercise.exercise_id,
                    "sets": sets,
                    "reps": reps,
                    "weight_used": 185,
                    "weight_unit": "lbs"
                }
            )
            
            assert response.status_code == 201
            data = response.get_json()
            actual_calories = data['data']['calories_burned']
            
            # Allow small rounding differences
            assert abs(actual_calories - expected_calories) < 1.0
