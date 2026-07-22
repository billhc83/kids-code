"""
routes/teacher_authoring.py's build() GET — build order step 4
(plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md §5): loading
project["draft_data"]["steps"] into the live workspace via
utils/teacher_authoring_serializer.py's hydrate_steps(), instead of only
ever starting from a blank Step 1. Also covers the raw-JSON view moving
behind `?raw=1` (kept reachable as the fallback the spec calls for).
"""

import json
import os
import re
import pytest
import responses

_AUTHORED_PROJECTS_URL = re.compile(
    re.escape(os.environ["SUPABASE_URL"]) + r"/rest/v1/authored_projects.*"
)


@pytest.fixture(autouse=True)
def _disable_csrf(app):
    app.config["WTF_CSRF_ENABLED"] = False

_GOOD_STEPS = [
    {
        "label": "Turn it on", "guidance": "guided", "view": "blocks",
        "global": [{"id": "g1", "kind": "leaf", "flag": "locked", "hint": None, "line": "int ledPin = 13;"}],
        "setup": [{"id": "s1", "kind": "leaf", "flag": "locked", "hint": None, "line": "pinMode(ledPin, OUTPUT);"}],
        "loop": [{"id": "l1", "kind": "leaf", "flag": "phantom", "hint": "Turn it on", "line": "digitalWrite(ledPin, HIGH);"}],
    }
]

_BAD_STEPS = [
    {
        "label": "Broken", "guidance": "guided", "view": "blocks",
        "global": [], "setup": [],
        "loop": [{
            "id": "if1", "kind": "compound", "compound_type": "ifblock",
            "flag": "phantom", "hint": "broken on purpose", "header": ")))not valid(((",
            "body": [{"id": "l1", "kind": "leaf", "flag": "locked", "hint": None, "line": "digitalWrite(2, HIGH);"}],
            "elseifs": [], "elsebody": None,
        }],
    }
]


def _project_row(steps):
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "created_by": "teacher-1",
        "project_key": "qa_project",
        "draft_data": {"steps": steps, "drawer": {}},
        "published_version": 0,
    }


def _login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "teacher-1"
        sess["username"] = "teacher1"
        sess["is_teacher"] = True
        sess["is_verified"] = True


def _config_from_body(body):
    m = re.search(r'window\.BB_CONFIG = (.*?);</script>', body, re.S)
    assert m, "expected an embedded window.BB_CONFIG script tag"
    return json.loads(m.group(1))


def test_existing_draft_hydrates_into_live_workspace(client, mock_supabase):
    row = _project_row(_GOOD_STEPS)
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    _login(client)

    resp = client.get(f"/teacher/projects/{row['id']}/build")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    config = _config_from_body(body)
    assert config["initial_steps"] is not None
    assert len(config["initial_steps"]) == 1
    step = config["initial_steps"][0]
    assert step["label"] == "Turn it on"
    assert step["sections"]["loop"][0]["type"] == "digitalwrite"
    assert step["sections"]["loop"][0]["flag"] == "phantom"

    # Raw JSON card is not shown by default.
    assert "Steps (JSON)" not in body
    assert 'href="?raw=1"' in body


def test_new_project_has_no_initial_steps(client, mock_supabase):
    row = _project_row([])
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    _login(client)

    resp = client.get(f"/teacher/projects/{row['id']}/build")
    assert resp.status_code == 200
    config = _config_from_body(resp.get_data(as_text=True))
    assert config["initial_steps"] is None


def test_unhydratable_draft_falls_back_to_blank_workspace_with_warning(client, mock_supabase):
    row = _project_row(_BAD_STEPS)
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    _login(client)

    resp = client.get(f"/teacher/projects/{row['id']}/build")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    config = _config_from_body(body)
    assert config["initial_steps"] is None
    assert "couldn't be loaded into the live" in body
    assert 'href="?raw=1"' in body


def test_raw_query_param_shows_json_textarea(client, mock_supabase):
    row = _project_row(_GOOD_STEPS)
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    _login(client)

    resp = client.get(f"/teacher/projects/{row['id']}/build?raw=1")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Steps (JSON)" in body
    assert "Turn it on" in body  # steps_json textarea content


# ── validate_step_shape() guardrail — enforced on save, not just in the
# settings-panel UI, so the raw-JSON fallback textarea can't smuggle in a
# combination the tool no longer offers (see also
# tests/test_teacher_authoring_serializer.py's direct unit tests). ─────────


def test_save_rejects_disallowed_guidance_without_touching_supabase(client, mock_supabase):
    row = _project_row([])
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    # Deliberately no PATCH/update mock registered — if save_draft() were
    # reached despite the bad shape, the unmocked request would error the
    # test, proving the guardrail runs before any persistence happens.
    _login(client)

    bad_steps = json.dumps([
        {"label": "S", "guidance": "full", "view": "blocks", "global": [], "setup": [], "loop": []}
    ])
    resp = client.post(f"/teacher/projects/{row['id']}/build", data={"steps_json": bad_steps})
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "guidance" in body and "full" in body and "isn" in body


def test_save_rejects_editor_view_without_touching_supabase(client, mock_supabase):
    row = _project_row([])
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    _login(client)

    bad_steps = json.dumps([
        {"label": "S", "guidance": "guided", "view": "editor", "global": [], "setup": [], "loop": []}
    ])
    resp = client.post(f"/teacher/projects/{row['id']}/build", data={"steps_json": bad_steps})
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "blocks&#39; view" in body


def test_publish_rejects_disallowed_guidance(client, mock_supabase):
    row = _project_row([
        {"label": "S", "guidance": "full", "view": "blocks", "global": [], "setup": [], "loop": []}
    ])
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)
    _login(client)

    resp = client.post(f"/teacher/projects/{row['id']}/publish", follow_redirects=True)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Publish failed" in body and "full" in body
