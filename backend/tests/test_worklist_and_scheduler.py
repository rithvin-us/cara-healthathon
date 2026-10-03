from conftest import open_visit

from app.models.models import NudgeLog


def test_worklist_summary_and_contents(client, coordinator):
    data = client.get("/api/v1/worklist", headers=coordinator).json()
    assert data["summary"] == {
        "overdue": 5,
        "due_today": 2,
        "high_risk": 2,
        "upcoming_7_days": data["summary"]["upcoming_7_days"],
    }
    names = [i["patient_name"] for i in data["items"]]
    assert names[:5] == ["Kavya Iyer", "Fatima Shaikh", "Sunita Rao", "Lakshmi Narayanan", "Priyanka Deshmukh"]
    assert set(names[5:]) == {"Anjali Patel", "Meera Kapoor"}
    assert "Rekha Yadav" not in names  # closed plan


def test_worklist_filters(client, coordinator):
    by_type = client.get("/api/v1/worklist", params={"visit_type": "6wk Checkup"}, headers=coordinator).json()
    assert [i["patient_name"] for i in by_type["items"]] == ["Kavya Iyer"]
    by_risk = client.get("/api/v1/worklist", params={"risk_flag": "hypertension"}, headers=coordinator).json()
    assert [i["patient_name"] for i in by_risk["items"]] == ["Sunita Rao"]
    assert by_risk["summary"]["overdue"] == 5  # summary ignores filters
    bad = client.get("/api/v1/worklist", params={"risk_flag": "unknown"}, headers=coordinator)
    assert bad.status_code == 422


def test_worklist_shows_last_reminder(client, coordinator):
    items = {i["patient_name"]: i for i in client.get("/api/v1/worklist", headers=coordinator).json()["items"]}
    assert items["Kavya Iyer"]["last_reminder_status"] == "read"
    assert items["Meera Kapoor"]["last_reminder_at"] is None


def test_daily_job_sends_each_scheduled_reminder_once(client, coordinator, db):
    first = client.post("/api/v1/admin/scheduler/run", headers=coordinator).json()
    # Meera (+husband) and Anjali are due today; Priyanka (+husband) just turned overdue.
    assert first["batch_nudges_sent"] == 5
    second = client.post("/api/v1/admin/scheduler/run", headers=coordinator).json()
    assert second["batch_nudges_sent"] == 0

    visit = open_visit(db, "Priyanka Deshmukh", "Weekly Risk Checkup (Week 1)")
    triggers = sorted(n.trigger for n in db.query(NudgeLog).filter_by(visit_id=visit.visit_id, recipient_type="mother"))
    assert triggers == ["due_today", "overdue"]


def test_revoked_family_member_gets_no_scheduled_reminder(client, coordinator, db):
    client.post("/api/v1/admin/scheduler/run", headers=coordinator)
    assert db.query(NudgeLog).filter_by(recipient_contact="+919820020102").count() == 0  # Zoya, consent withdrawn


def test_cron_endpoint_requires_secret(client):
    assert client.get("/api/v1/internal/cron/daily").status_code == 401
    assert client.get("/api/v1/internal/cron/daily", headers={"Authorization": "Bearer wrong"}).status_code == 401
    ok = client.get("/api/v1/internal/cron/daily", headers={"Authorization": "Bearer test-cron-secret"})
    assert ok.status_code == 200 and ok.json()["batch_nudges_sent"] == 5


def test_digest_counts_only_this_facility(client, coordinator):
    digest = client.get("/api/v1/admin/digest", headers=coordinator).json()
    assert digest["overdue_count"] == 5 and digest["due_today_count"] == 2
    assert digest["is_fallback_used"] is False
