import pytest
from conftest import open_visit, patient_named

from app.models.models import AuditLog, AuditLogImmutableError


def test_other_facility_sees_nothing(client, other_facility, db):
    patient = patient_named(db, "Sunita Rao")
    visit = open_visit(db, "Sunita Rao", "Weekly Risk Checkup (Week 2)")
    member = patient.family_members[0]

    assert client.get(f"/api/v1/patients/{patient.patient_id}", headers=other_facility).status_code == 404
    assert client.get(f"/api/v1/audit-log/patients/{patient.patient_id}", headers=other_facility).status_code == 404
    assert client.get("/api/v1/worklist", headers=other_facility).json()["items"] == []
    assert client.post(f"/api/v1/visits/{visit.visit_id}/nudge", headers=other_facility).status_code == 404
    assert client.get(f"/api/v1/visits/{visit.visit_id}/message-preview", headers=other_facility).status_code == 404
    assert (
        client.post(
            f"/api/v1/visits/{visit.visit_id}/complete", json={"completed_date": "2026-01-01"}, headers=other_facility
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/family-members/{member.family_id}/consent", json={"consent_given": False}, headers=other_facility
        ).status_code
        == 404
    )
    assert client.get("/api/v1/admin/digest", headers=other_facility).json()["overdue_count"] == 0


def test_other_facility_scheduler_does_not_touch_our_mothers(client, other_facility):
    assert client.post("/api/v1/admin/scheduler/run", headers=other_facility).json()["batch_nudges_sent"] == 0


def test_patient_audit_trail_is_filtered(client, coordinator, db):
    patient = patient_named(db, "Fatima Shaikh")
    logs = client.get(f"/api/v1/audit-log/patients/{patient.patient_id}", headers=coordinator).json()
    assert logs and all(entry["patient_id"] == patient.patient_id for entry in logs)
    assert {"CREATE_DISCHARGE_PLAN", "REVOKE_CONSENT", "TRIGGER_NUDGE"} <= {e["action"] for e in logs}
    assert {e["actor_name"] for e in logs} >= {"Dr. Ananya Sharma", "Priya Patel", "System"}


def test_facility_audit_log_role_and_scope(client, admin, coordinator, other_facility):
    assert client.get("/api/v1/audit-log", headers=coordinator).status_code == 403
    assert len(client.get("/api/v1/audit-log", params={"limit": 5}, headers=admin).json()) == 5


def test_audit_log_is_append_only(db):
    entry = db.query(AuditLog).first()
    entry.details = "tampered"
    with pytest.raises(AuditLogImmutableError):
        db.flush()
    db.rollback()
    entry = db.query(AuditLog).first()
    db.delete(entry)
    with pytest.raises(AuditLogImmutableError):
        db.flush()
    db.rollback()
