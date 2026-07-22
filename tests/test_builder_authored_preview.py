"""
routes/builder.py's builder_endpoint() (/builder) draft-preview branch —
plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md's "full-interface preview"
follow-on. arduino_interface.html's loadBlockBuilder() always fetches
/builder?preset=<val>&page=<val>; teacher_authoring.preview() passes an
authored_projects row id as `preset` instead of a utils/project_registry.py
or utils/presets.py key. builder_endpoint() must recognize that, build the
real progression config from the draft (materialize()+parse_steps(), same as
what teacher_authoring.preview() already validates), enforce ownership, and
otherwise fall through to the existing preset-registry path unchanged.
"""

import json
import os
import re
import pytest
import responses

_AUTHORED_PROJECTS_URL = re.compile(
    re.escape(os.environ["SUPABASE_URL"]) + r"/rest/v1/authored_projects.*"
)

_STEPS = [
    {
        "label": "Turn it on", "guidance": "guided", "view": "blocks",
        "global": [{"id": "g1", "kind": "leaf", "flag": "locked", "hint": None, "line": "int ledPin = 13;"}],
        "setup": [{"id": "s1", "kind": "leaf", "flag": "locked", "hint": None, "line": "pinMode(ledPin, OUTPUT);"}],
        "loop": [{"id": "l1", "kind": "leaf", "flag": "phantom", "hint": "Turn it on", "line": "digitalWrite(ledPin, HIGH);"}],
    }
]


def _authored_project_row(owner_id):
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "created_by": owner_id,
        "project_key": "qa_project",
        "draft_data": {"steps": _STEPS, "drawer": {}},
        "published_version": 0,
    }


def test_owned_draft_builds_progression_config_from_materialize(client, mock_supabase):
    row = _authored_project_row("teacher-1")
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)

    with client.session_transaction() as sess:
        sess["user_id"] = "teacher-1"
        sess["username"] = "teacher1"
        sess["is_teacher"] = True
        sess["is_verified"] = True

    resp = client.get(f"/builder?preset={row['id']}&page={row['id']}")
    assert resp.status_code == 200

    body = resp.get_data(as_text=True)
    m = re.search(r'id="bb-config-json">(.*?)</script>', body, re.S)
    assert m, "expected an embedded bb-config-json script tag"
    config = json.loads(m.group(1))

    assert config["mode"] == "progression"
    assert config["page"] == "qa_project"
    # Step 0 (authored) + Mission Complete, same as materialize()+parse_steps() elsewhere in this suite.
    assert len(config["steps"]) == 2
    assert config["steps"][0]["label"] == "Turn it on"


def test_unowned_draft_falls_through_to_registry_preset(client, mock_supabase):
    row = _authored_project_row("someone-else")
    mock_supabase.add(responses.GET, _AUTHORED_PROJECTS_URL, json=[row], status=200)

    with client.session_transaction() as sess:
        sess["user_id"] = "teacher-1"
        sess["username"] = "teacher1"
        sess["is_teacher"] = True
        sess["is_verified"] = True

    # Not this session's draft — must not leak it. Falls through to
    # build_config(preset=<the draft's own id string>), which won't resolve
    # against PROJECTS/PRESETS either, so this raises the same
    # "unknown preset" error an unresolvable preset key always does (Flask's
    # TESTING config propagates unhandled view exceptions to the caller
    # rather than turning them into a 500 response) — not silently serving
    # someone else's draft.
    with pytest.raises(ValueError, match="Unknown block builder preset"):
        client.get(f"/builder?preset={row['id']}&page={row['id']}")


def test_non_uuid_preset_falls_through_to_existing_registry_path(client, mock_supabase):
    # A normal preset key fails UUID casting against authored_projects.id —
    # must be swallowed and treated as "not a draft", not surfaced as a 500.
    mock_supabase.add(
        responses.GET, _AUTHORED_PROJECTS_URL,
        json={"message": "invalid input syntax for type uuid"}, status=400,
    )

    with client.session_transaction() as sess:
        sess["user_id"] = "teacher-1"
        sess["username"] = "teacher1"
        sess["is_teacher"] = True
        sess["is_verified"] = True

    resp = client.get("/builder?preset=codebreaker&page=codebreaker")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    m = re.search(r'id="bb-config-json">(.*?)</script>', body, re.S)
    assert m
    config = json.loads(m.group(1))
    assert config["page"] == "codebreaker"
