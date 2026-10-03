import csv
import io
from datetime import date

import pytest
from conftest import patient_named

from app.services import message_templates
from app.services.calendar_engine import DEFAULT_SCHEDULE, RISK_SCHEDULES
from app.services.content_filter import ContentFilter

# --- family & consent -------------------------------------------------------


def test_family_member_validation(client, coordinator, db):
    patient = patient_named(db, "Sunita Rao")
    url = f"/api/v1/patients/{patient.patient_id}/family-members"
    base = {"name": "Someone", "relation": "Sister", "consent_given": True}
    assert (
        client.post(url, json={**base, "contact_number": patient.contact_number}, headers=coordinator).status_code
        == 422
    )
    assert client.post(url, json={**base, "contact_number": "+919820020103"}, headers=coordinator).status_code == 409
    assert client.post(url, json={**base, "contact_number": "abc"}, headers=coordinator).status_code == 422


def test_family_member_inherits_mother_language(client, coordinator, db):
    patient = patient_named(db, "Lakshmi Narayanan")
    res = client.post(
        f"/api/v1/patients/{patient.patient_id}/family-members",
        json={"name": "Karthik", "relation": "Husband", "contact_number": "+919820030104"},
        headers=coordinator,
    )
    assert res.json()["preferred_language"] == "Tamil"


# --- reports ----------------------------------------------------------------


def test_coordinator_cannot_view_reports(client, coordinator):
    assert client.get("/api/v1/reports/outcomes", headers=coordinator).status_code == 403


def test_anonymised_csv_has_no_identifiers(client, doctor):
    res = client.get("/api/v1/reports/outcomes", params={"export": "csv", "anonymize": True}, headers=doctor)
    assert res.status_code == 200 and res.headers["content-type"].startswith("text/csv")
    body = res.text
    assert "Sunita" not in body and "+91" not in body
    rows = list(csv.reader(io.StringIO(body)))
    assert rows[0] == ["visit_ref", "visit_type", "due_date", "status", "completed_date"]
    assert rows[1][0] == "V0001"


def test_identified_csv_is_admin_only(client, doctor, admin):
    params = {"export": "csv", "anonymize": False}
    assert client.get("/api/v1/reports/outcomes", params=params, headers=doctor).status_code == 403
    res = client.get("/api/v1/reports/outcomes", params=params, headers=admin)
    assert res.status_code == 200 and "Sunita Rao" in res.text


def test_report_date_range(client, admin):
    assert (
        client.get(
            "/api/v1/reports/outcomes", params={"start_date": "2026-05-01", "end_date": "2026-04-01"}, headers=admin
        ).status_code
        == 422
    )
    empty = client.get(
        "/api/v1/reports/outcomes", params={"start_date": "2020-01-01", "end_date": "2020-01-31"}, headers=admin
    ).json()
    assert empty["total_visits"] == 0 and empty["overall_completion_rate_pct"] == 0.0


# --- staff admin ------------------------------------------------------------


def test_create_staff_account_and_sign_in(client, admin):
    new = {"name": "Dr. Sangeeta Joshi", "role": "Doctor", "email": "Sangeeta@Cara.Health", "password": "a-strong-pass"}
    res = client.post("/api/v1/admin/staff", json=new, headers=admin)
    assert res.status_code == 201 and res.json()["email"] == "sangeeta@cara.health"
    assert client.post("/api/v1/admin/staff", json=new, headers=admin).status_code == 409
    login = client.post("/api/v1/auth/login", json={"email": "sangeeta@cara.health", "password": "a-strong-pass"})
    assert login.status_code == 200


@pytest.mark.parametrize(
    "override", [{"password": "short"}, {"role": "Superuser"}, {"email": "not-an-email"}, {"name": "A"}]
)
def test_create_staff_validation(client, admin, override):
    body = {
        "name": "New Nurse",
        "role": "Coordinator",
        "email": "nurse@cara.health",
        "password": "long-enough-1",
        **override,
    }
    assert client.post("/api/v1/admin/staff", json=body, headers=admin).status_code == 422


def test_admin_cannot_turn_off_self(client, admin, demo_data):
    res = client.patch(f"/api/v1/admin/staff/{demo_data['admin_user_id']}/toggle-active", headers=admin)
    assert res.status_code == 409


def test_staff_endpoints_are_admin_only(client, doctor):
    assert client.get("/api/v1/admin/staff", headers=doctor).status_code == 403


def test_demo_reset(client, admin, coordinator, db):
    patient = patient_named(db, "Meera Kapoor")
    visit = patient.discharge_plans[-1].visits[1]
    client.post(f"/api/v1/visits/{visit.visit_id}/missed", json={"reason": "declined"}, headers=coordinator)
    assert client.post("/api/v1/admin/demo/reset", headers=admin).json()["patients"] == 10
    items = client.get("/api/v1/worklist", headers=coordinator).json()["items"]
    assert "Meera Kapoor" in {i["patient_name"] for i in items}


def test_demo_reset_disabled_outside_demo_mode(client, admin, demo_mode_off):
    assert client.post("/api/v1/admin/demo/reset", headers=admin).status_code == 404


# --- message safety ---------------------------------------------------------


@pytest.mark.parametrize("language", ["English", "Hindi", "Tamil"])
def test_every_template_passes_the_content_filter(language):
    visit_types = [t for t, _ in DEFAULT_SCHEDULE] + [t for sched in RISK_SCHEDULES.values() for t, _ in sched]
    for kind in ("mother_due", "mother_overdue", "family", "family_overdue"):
        for visit_type in visit_types:
            text = message_templates.render(
                kind,
                language,
                name="Asha",
                facility="City Hospital",
                visit_type=visit_type,
                due_date=date(2026, 10, 3),
                mother="Meera",
            )
            ok, reason = ContentFilter.inspect_text(text)
            assert ok, (language, kind, visit_type, reason)
            assert visit_type not in text  # internal visit codes never leak into messages
