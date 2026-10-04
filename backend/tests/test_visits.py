from datetime import timedelta

import pytest
from conftest import open_visit

from app.core.clock import facility_today


def _complete(client, headers, visit_id, **body):
    payload = {"completed_date": facility_today().isoformat(), **body}
    return client.post(f"/api/v1/visits/{visit_id}/complete", json=payload, headers=headers)


@pytest.mark.parametrize(
    "note",
    ["Prescribed iron tablets", "BP 150/100, refer", "Started antibiotics for infection", "Give 5 ml syrup"],
)
def test_clinical_notes_are_rejected(client, coordinator, db, note):
    visit = open_visit(db, "Meera Kapoor", "48-72h Checkup")
    res = _complete(client, coordinator, visit.visit_id, note=note)
    assert res.status_code == 422
    assert "logistics only" in res.json()["detail"]


def test_logistics_note_is_saved(client, coordinator, db):
    visit = open_visit(db, "Meera Kapoor", "48-72h Checkup")
    res = _complete(client, coordinator, visit.visit_id, note="Home visit by ASHA worker")
    assert res.status_code == 200
    db.refresh(visit)
    assert visit.note == "Home visit by ASHA worker" and visit.status == "completed"


def test_cannot_complete_twice_or_in_future(client, coordinator, db):
    visit = open_visit(db, "Meera Kapoor", "48-72h Checkup")
    future = (facility_today() + timedelta(days=1)).isoformat()
    assert _complete(client, coordinator, visit.visit_id, completed_date=future).status_code == 422
    assert _complete(client, coordinator, visit.visit_id).status_code == 200
    assert _complete(client, coordinator, visit.visit_id).status_code == 409


def test_mark_missed_with_reason(client, coordinator, db):
    visit = open_visit(db, "Kavya Iyer", "6wk Checkup")
    res = client.post(f"/api/v1/visits/{visit.visit_id}/missed", json={"reason": "moved"}, headers=coordinator)
    assert res.status_code == 200 and res.json()["status"] == "missed"
    db.refresh(visit)
    assert visit.note == "Missed: moved away"
    bad = client.post(f"/api/v1/visits/{visit.visit_id}/missed", json={"reason": "sick"}, headers=coordinator)
    assert bad.status_code in (409, 422)


def test_reschedule_visit(client, coordinator, db):
    visit = open_visit(db, "Kavya Iyer", "6wk Checkup")
    new_date = (facility_today() + timedelta(days=2)).isoformat()
    res = client.patch(f"/api/v1/visits/{visit.visit_id}/reschedule", json={"due_date": new_date}, headers=coordinator)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "upcoming" and res.json()["due_date"] == new_date


def test_admin_cannot_reschedule(client, admin, db):
    visit = open_visit(db, "Kavya Iyer", "6wk Checkup")
    res = client.patch(
        f"/api/v1/visits/{visit.visit_id}/reschedule", json={"due_date": facility_today().isoformat()}, headers=admin
    )
    assert res.status_code == 403


@pytest.mark.parametrize(
    "name,visit_type,greeting",
    [
        ("Sunita Rao", "Weekly Risk Checkup (Week 2)", "नमस्ते"),
        ("Lakshmi Narayanan", "7-14d Checkup", "வணக்கம்"),
        ("Meera Kapoor", "48-72h Checkup", "Hello"),
        ("Priyanka Deshmukh", "Weekly Risk Checkup (Week 1)", "Hello"),  # Marathi falls back to English
    ],
)
def test_message_preview_uses_preferred_language(client, coordinator, db, name, visit_type, greeting):
    visit = open_visit(db, name, visit_type)
    res = client.get(f"/api/v1/visits/{visit.visit_id}/message-preview", headers=coordinator)
    assert res.status_code == 200
    body = res.json()
    assert body["message_text"].startswith(greeting) and body["provider"] == "simulated"


def test_overdue_message_says_was_due(client, coordinator, db):
    visit = open_visit(db, "Kavya Iyer", "6wk Checkup")
    kavya = client.get(f"/api/v1/visits/{visit.visit_id}/message-preview", headers=coordinator).json()
    assert "இருந்தது" in kavya["message_text"]  # Tamil "was" (overdue wording)


def test_cannot_nudge_a_closed_visit(client, coordinator, db):
    visit = open_visit(db, "Divya Menon", "24h Checkup")
    assert client.post(f"/api/v1/visits/{visit.visit_id}/nudge", headers=coordinator).status_code == 409
