import pytest
import responses
import os
import re

def test_admin_access_denied_for_student(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "student-123"
        sess["username"] = "student"
        sess["is_admin"] = False
        sess["is_verified"] = True

    response = client.get("/admin")
    assert response.status_code in [302, 403]

def test_admin_dashboard_renders(client, mock_supabase):
    with client.session_transaction() as sess:
        sess["user_id"] = "admin-123"
        sess["username"] = "admin"
        sess["is_admin"] = True
        sess["is_verified"] = True

    # Use match_querystring=False and register multiple times or use a more permissive matcher
    # Registering mocks with a high match count to avoid "Not all requests executed" or "Connection Refused"
    
    base_url = os.environ['SUPABASE_URL']
    
    # helper to register permissive mocks
    def add_mock(path, json_data=[]):
        mock_supabase.add(
            responses.GET,
            re.compile(f"{re.escape(base_url)}{path}.*"),
            json=json_data,
            status=200,
            match_querystring=False
        )

    add_mock("/rest/v1/feedback_threads", [{"id": "t1", "username": "u1", "category": "Bug", "subject": "S1", "status": "open"}])
    add_mock("/rest/v1/feedback_messages")
    add_mock("/rest/v1/challenge_submissions")
    add_mock("/rest/v1/activity_logs")
    add_mock("/rest/v1/users", [{"id": "user-1", "username": "user1", "email": "user1@example.com", "created_at": "2024-01-01"}])
    
    # 7. get_completed_lessons & get_user_progression -> progression
    def progression_mock(request):
        print(f"DEBUG PROGRESSION: {request.url}")
        return (200, {}, "[]")

    mock_supabase.add_callback(
        responses.GET,
        re.compile(f"{re.escape(base_url)}/rest/v1/progression.*"),
        callback=progression_mock,
        match_querystring=False
    )

    # Also mock user_badges for context processor
    add_mock("/rest/v1/user_badges")

    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data
