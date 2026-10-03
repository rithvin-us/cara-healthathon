"""SRS acceptance tests TC-01 to TC-10 (see docs/srs-traceability.md)."""

from datetime import timedelta

from conftest import open_visit, patient_named

from app.core.clock import facility_today
from app.models.models import AuditLog
from app.services.content_filter import ContentFilter
from app.services.nudge_engine import NudgeEngine


def _new_mother(**overrides):
    today = facility_today()
    payload = {
        "name": "Pooja Sharma",
        "contact_number": "+919988776655",
        "preferred_language": "English",
        "delivery_date": (today - timedelta(days=2)).isoformat(),
        "discharge_date": today.isoformat(),
        "newborn_gender": "Female",
        "newborn_name": "Baby Sharma",
        "risk_flags": [],
    }
    payload.update(overrides)
    return payload


def test_tc01_create_discharge_plan_with_who_defaults(client, doctor):
    res = client.post("/api/v1/patients", json=_new_mother(), headers=doctor)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["patient"]["name"] == "Pooja Sharma"
    types = [v["visit_type"] for v in data["active_plan"]["visits"]]
    assert types == ["24h Checkup", "48-72h Checkup", "7-14d Checkup", "6wk Checkup"]
    assert data["newborns"][0]["name_or_initial"] == "Baby Sharma"


def test_tc02_hypertension_flag_adds_weekly_visits(client, doctor):
    res = client.post(
        "/api/v1/patients",
        json=_new_mother(contact_number="+919876500112", risk_flags=["hypertension"]),
        headers=doctor,
    )
    assert res.status_code == 201, res.text
    types = [v["visit_type"] for v in res.json()["active_plan"]["visits"]]
    assert sum("Weekly Risk Checkup" in t for t in types) == 4
    assert "6wk Checkup" in types and len(types) == 8


def test_tc03_daily_job_computes_statuses(client, coordinator, db):
    res = client.post("/api/v1/admin/scheduler/run", headers=coordinator)
    assert res.status_code == 200
    today = facility_today()
    for name, visit_type, expected in [
        ("Meera Kapoor", "48-72h Checkup", "due_today"),
        ("Kavya Iyer", "6wk Checkup", "overdue"),
        ("Divya Menon", "6wk Checkup", "upcoming"),
    ]:
        visit = open_visit(db, name, visit_type)
        assert visit.status == expected, (name, visit.due_date, today)


def test_tc04_mark_visit_complete_writes_audit(client, coordinator, db):
    visit = open_visit(db, "Meera Kapoor", "48-72h Checkup")
    res = client.post(
        f"/api/v1/visits/{visit.visit_id}/complete",
        json={"completed_date": facility_today().isoformat(), "note": "Seen at OPD with her husband"},
        headers=coordinator,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "completed"
    entry = db.get(AuditLog, body["audit_id"])
    assert entry.action == "MARK_VISIT_COMPLETE" and entry.entity_id == visit.visit_id


def test_tc05_worklist_is_ranked_by_days_overdue(client, coordinator):
    res = client.get("/api/v1/worklist", headers=coordinator)
    assert res.status_code == 200
    days = [item["days_overdue"] for item in res.json()["items"]]
    assert days == sorted(days, reverse=True)
    assert res.json()["items"][0]["patient_name"] == "Kavya Iyer"


def test_tc06_manual_nudge_reaches_mother_and_consented_family(client, coordinator, db):
    visit = open_visit(db, "Sunita Rao", "Weekly Risk Checkup (Week 2)")
    res = client.post(f"/api/v1/visits/{visit.visit_id}/nudge", headers=coordinator)
    assert res.status_code == 200, res.text
    nudges = res.json()
    assert {n["recipient_type"] for n in nudges} == {"mother", "family"}
    assert all(n["message_text"] for n in nudges)
    assert nudges[0]["message_text"].startswith("नमस्ते Sunita Rao")  # her preferred language is Hindi


def test_tc07_add_family_member_with_consent(client, coordinator, db):
    patient = patient_named(db, "Anjali Patel")
    res = client.post(
        f"/api/v1/patients/{patient.patient_id}/family-members",
        json={"name": "Rakesh Patel", "relation": "Husband", "contact_number": "98200 30106", "consent_given": True},
        headers=coordinator,
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["latest_consent"] is True
    assert data["contact_number"] == "+919820030106"


def test_tc08_revoked_consent_stops_family_nudges(client, coordinator, db):
    patient = patient_named(db, "Sunita Rao")
    member = patient.family_members[0]
    res = client.patch(
        f"/api/v1/family-members/{member.family_id}/consent", json={"consent_given": False}, headers=coordinator
    )
    assert res.status_code == 200 and res.json()["latest_consent"] is False
    assert NudgeEngine.is_family_consent_active(db, member.family_id) is False

    visit = open_visit(db, "Sunita Rao", "Weekly Risk Checkup (Week 2)")
    nudges = client.post(f"/api/v1/visits/{visit.visit_id}/nudge", headers=coordinator).json()
    assert [n["recipient_type"] for n in nudges] == ["mother"]


def test_tc09_outcomes_report(client, admin):
    res = client.get("/api/v1/reports/outcomes", headers=admin)
    assert res.status_code == 200
    report = res.json()
    assert report["total_patients"] == 10
    assert report["completed_visits"] > 0
    assert report["outcomes_by_visit_type"][0]["visit_type"] == "24h Checkup"


def test_tc10_content_filter_rejects_clinical_terms():
    bad = "Mother should take 500mg dosage medicine for infection treatment."
    ok, reason = ContentFilter.inspect_text(bad)
    assert ok is False and "Disallowed clinical term" in reason

    text, used_fallback = ContentFilter.filter_and_fallback_nudge(
        bad, mother_name="Pooja", visit_type="24-hour checkup", due_date="25 Sep 2026", facility_name="City Hospital"
    )
    assert used_fallback is True
    assert "dosage" not in text and "Pooja" in text and "24-hour checkup" in text
