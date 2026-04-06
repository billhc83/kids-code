import pytest
import responses
import bcrypt
from flask import session

def test_login_success(client, mock_supabase):
    # Setup mock user
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-123",
        "username": "testuser",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": True
    }
    
    # Mock Supabase GET user
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.testuser&limit=1",
        json=[mock_user],
        status=200
    )
    
    # Mock seed_first_lesson -> unlock_lesson
    # 1. Check if lesson exists
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/progression?user_id=eq.user-123&lesson_key=eq.getting_started",
        json=[], # Not found
        status=200
    )
    # 2. POST to creates it
    mock_supabase.add(
        responses.POST,
        "https://mock-project.supabase.co/rest/v1/progression",
        json=[],
        status=201
    )

    response = client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")
    with client.session_transaction() as sess:
        assert sess["user_id"] == "user-123"
        assert sess["username"] == "testuser"

def test_login_invalid_password(client, mock_supabase):
    hashed = bcrypt.hashpw("correct-password".encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-123",
        "username": "testuser",
        "password_hash": hashed,
        "is_verified": True
    }
    
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.testuser&limit=1",
        json=[mock_user],
        status=200
    )

    response = client.post("/login", data={
        "username": "testuser",
        "password": "wrong-password"
    })

    assert b"Incorrect password" in response.data

def test_register_success(client, mock_supabase):
    # Mock username check (should return empty list)
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.newuser&limit=1",
        json=[],
        status=200
    )
    
    # Mock user creation
    mock_supabase.add(
        responses.POST,
        "https://mock-project.supabase.co/rest/v1/users",
        json=[{"id": "new-user-id", "verification_token": "mock-token"}],
        status=201
    )
    
    # Mock Resend email
    mock_supabase.add(
        responses.POST,
        "https://api.resend.com/emails",
        json={},
        status=200
    )

    response = client.post("/register", data={
        "email": "test@example.com",
        "username": "newuser",
        "password": "password123",
        "is_parent": "false"
    })

    assert response.status_code == 302
    assert response.location.endswith("/check-email")
