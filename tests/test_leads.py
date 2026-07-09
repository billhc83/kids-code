"""
tests/test_leads.py — unit tests for utils/leads.py against a mocked
Supabase REST API (see tests/conftest.py's `mock_supabase` fixture, same
pattern used by tests/test_help_kb.py).
"""

from utils import leads


def test_create_lead_inserts_and_returns_row(mock_supabase):
    mock_supabase.add(
        "POST",
        "https://mock-project.supabase.co/rest/v1/leads",
        json=[{"id": "lead-1", "email": "parent@example.com", "source": "try_page"}],
        status=201,
    )
    row = leads.create_lead("parent@example.com")
    assert row["id"] == "lead-1"
    assert row["email"] == "parent@example.com"


def test_get_unfollowed_leads_returns_rows(mock_supabase):
    mock_supabase.add(
        "GET",
        "https://mock-project.supabase.co/rest/v1/leads?select=%2A&followed_up_at=is.null",
        json=[{"id": "lead-1", "email": "a@example.com", "followed_up_at": None}],
        status=200,
    )
    rows = leads.get_unfollowed_leads()
    assert len(rows) == 1
    assert rows[0]["email"] == "a@example.com"


def test_email_exists_in_users_true(mock_supabase):
    mock_supabase.add(
        "GET",
        "https://mock-project.supabase.co/rest/v1/users?select=id&email=eq.parent%40example.com",
        json=[{"id": "user-1"}],
        status=200,
    )
    assert leads.email_exists_in_users("parent@example.com") is True


def test_email_exists_in_users_false(mock_supabase):
    mock_supabase.add(
        "GET",
        "https://mock-project.supabase.co/rest/v1/users?select=id&email=eq.nobody%40example.com",
        json=[],
        status=200,
    )
    assert leads.email_exists_in_users("nobody@example.com") is False
