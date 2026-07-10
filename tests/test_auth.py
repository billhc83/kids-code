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

def _mock_valid_invite(mock_supabase, token, email):
    mock_supabase.add(
        responses.GET,
        f"https://mock-project.supabase.co/rest/v1/registration_invites?token=eq.{token}&limit=1",
        json=[{"token": token, "email": email, "used_at": None,
               "expires_at": "2999-01-01T00:00:00+00:00"}],
        status=200
    )
    mock_supabase.add(
        responses.PATCH,
        "https://mock-project.supabase.co/rest/v1/registration_invites",
        json=[{"token": token}],
        status=200
    )


def test_register_success(client, mock_supabase):
    _mock_valid_invite(mock_supabase, "valid-tok", "test@example.com")

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
        "token": "valid-tok",
        "email": "test@example.com",
        "username": "newuser",
        "password": "password123",
        "is_parent": "false",
        "agree_tos": "true",
    })

    assert response.status_code == 302
    assert "/subscribe/checkout" in response.location


def test_register_redirects_to_checkout(client, mock_supabase):
    _mock_valid_invite(mock_supabase, "valid-tok-2", "test2@example.com")

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
        "token": "valid-tok-2",
        "email": "test2@example.com", "username": "newuser2", "password": "password123",
        "is_parent": "false", "agree_tos": "true",
    })
    assert response.status_code == 302
    assert "/subscribe/checkout" in response.location


def test_register_post_rejects_missing_token(client, mock_supabase):
    response = client.post("/register", data={
        "token": "",
        "email": "nope@example.com", "username": "newuser3", "password": "password123",
        "is_parent": "false", "agree_tos": "true",
    })
    assert response.status_code == 302
    assert "/register/invite" in response.location


def test_register_get_redirects_without_valid_token(client, mock_supabase):
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/registration_invites?token=eq.bad-tok&limit=1",
        json=[],
        status=200
    )
    response = client.get("/register?token=bad-tok")
    assert response.status_code == 302
    assert "/register/invite" in response.location


def test_register_invite_post_always_shows_generic_confirmation(client, mock_supabase, monkeypatch):
    monkeypatch.setattr("routes.auth.send_registration_invite_email", lambda email, token: None)
    mock_supabase.add(
        responses.POST,
        "https://mock-project.supabase.co/rest/v1/registration_invites",
        json=[{"token": "new-tok"}],
        status=201
    )
    response = client.post("/register/invite", data={"email": "someone@example.com"})
    assert response.status_code == 200
    assert b"Check Your Email" in response.data


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


def test_login_shows_subscription_gate_not_verify_email_when_both_pending(client, mock_supabase):
    # A standard signup's verification email is only sent by the Stripe webhook
    # (routes/billing.py's handle_checkout_completed) — before checkout completes, the
    # account is always both unverified AND subscription_status='pending'. The subscription
    # check must win here: telling someone to "check your email for a link" is false when
    # no link was ever sent, and masks the real blocker (no active subscription).
    hashed = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-999",
        "username": "unpaiduser",
        "password_hash": hashed,
        "is_parent": False,
        "is_admin": False,
        "is_verified": False,
        "user_type": "standard",
        "subscription_status": "pending",
    }
    mock_supabase.add(
        responses.GET,
        "https://mock-project.supabase.co/rest/v1/users?username=eq.unpaiduser&limit=1",
        json=[mock_user],
        status=200
    )

    response = client.post("/login", data={"username": "unpaiduser", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe/pending" in response.location
    with client.session_transaction() as sess:
        assert "pending_email" not in sess


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
