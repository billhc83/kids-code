import pytest
import responses
import bcrypt
from flask import session


@pytest.fixture(autouse=True)
def _disable_csrf(app):
    app.config["WTF_CSRF_ENABLED"] = False


def test_login_success(client, mock_supabase):
    # Setup mock user
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-123",
        "username": "testuser",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": True,
        "user_type": "standard",
        "subscription_status": "active",
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

    response = client.post("/register", data={
        "email": "test@example.com",
        "username": "newuser",
        "password": "password123",
        "is_parent": "false",
        "agree_tos": "true",
    })

    assert response.status_code == 302
    assert "/subscribe/checkout" in response.location


def test_register_redirects_to_checkout(client, mock_supabase):
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.newuser2&limit=1",
        json=[],
        status=200
    )
    mock_supabase.add(
        responses.POST,
        "https://mock-project.supabase.co/rest/v1/users",
        json=[{"id": "new-user-id-2", "verification_token": "mock-token-2"}],
        status=201
    )

    response = client.post("/register", data={
        "email": "test2@example.com", "username": "newuser2", "password": "password123",
        "is_parent": "false", "agree_tos": "true",
    })
    assert response.status_code == 302
    assert "/subscribe/checkout" in response.location


def test_login_blocks_standard_user_without_active_subscription(client, mock_supabase):
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-456",
        "username": "pendinguser",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": True,
        "user_type": "standard",
        "subscription_status": "pending",
    }
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.pendinguser&limit=1",
        json=[mock_user],
        status=200
    )

    response = client.post("/login", data={"username": "pendinguser", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe/pending" in response.location


def test_login_allows_provisioned_user_regardless_of_subscription_status(client, mock_supabase):
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-789",
        "username": "classuser",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": True,
        "user_type": "class",
        "subscription_status": "none",
        "is_teacher": False,
        "first_login_completed": True,
        "agreed_at": "2026-01-01T00:00:00+00:00",
    }
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.classuser&limit=1",
        json=[mock_user],
        status=200
    )
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/progression?user_id=eq.user-789&lesson_key=eq.getting_started",
        json=[],
        status=200
    )
    mock_supabase.add(
        responses.POST,
        "https://mock-project.supabase.co/rest/v1/progression",
        json=[],
        status=201
    )

    response = client.post("/login", data={"username": "classuser", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe" not in response.location


def test_login_blocks_linked_student_when_parent_subscription_inactive(client, mock_supabase, monkeypatch):
    # Parent-created student sub-accounts (utils.auth.create_student_for_parent) default
    # to subscription_status='none' on their own row — access should ride on the linking
    # parent's live status, checked via routes.auth.get_linking_parent.
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_student = {
        "id": "student-1",
        "username": "kiduser",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": True,
        "user_type": "standard",
        "subscription_status": "none",
    }
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.kiduser&limit=1",
        json=[mock_student],
        status=200
    )
    monkeypatch.setattr(
        "routes.auth.get_linking_parent",
        lambda student_id: {"id": "parent-1", "subscription_status": "canceled"},
    )

    response = client.post("/login", data={"username": "kiduser", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe/pending" in response.location
    with client.session_transaction() as sess:
        # Resuming Checkout from this page must act on the PARENT's account, not the
        # student's (the student has no real email/payment method of its own).
        assert sess["pending_subscription_user_id"] == "parent-1"


def test_login_allows_linked_student_when_parent_subscription_active(client, mock_supabase, monkeypatch):
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_student = {
        "id": "student-2",
        "username": "kiduser2",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": True,
        "user_type": "standard",
        "subscription_status": "none",
        "is_teacher": False,
        "first_login_completed": True,
        "agreed_at": "2026-01-01T00:00:00+00:00",
    }
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.kiduser2&limit=1",
        json=[mock_student],
        status=200
    )
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/progression?user_id=eq.student-2&lesson_key=eq.getting_started",
        json=[],
        status=200
    )
    mock_supabase.add(
        responses.POST,
        "https://mock-project.supabase.co/rest/v1/progression",
        json=[],
        status=201
    )
    monkeypatch.setattr(
        "routes.auth.get_linking_parent",
        lambda student_id: {"id": "parent-2", "subscription_status": "active"},
    )

    response = client.post("/login", data={"username": "kiduser2", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe" not in response.location
