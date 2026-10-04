"""The demo walkthrough (docs/demo-script.md) as one test, so the recorded
flow is proven end to end on every CI run."""

from datetime import timedelta

from app.core.clock import facility_today


def _quick(client, role):
    token = client.post("/api/v1/auth/quick-login", json={"role": role}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_demo_walkthrough(client):
    today = facility_today()

    # 1. Doctor discharges a high-risk mother; the preview equals the saved schedule.
    doctor = _quick(client, "Doctor")
    delivery = (today - timedelta(days=1)).isoformat()
    preview = client.post(
        "/api/v1/schedule/preview", json={"delivery_date": delivery, "risk_flags": ["hypertension"]}, headers=doctor
    ).json()
    created = client.post(
        "/api/v1/patients",
        json={
            "name": "Revathi Subramanian",
            "contact_number": "98200 55501",
            "preferred_language": "Tamil",
            "delivery_date": delivery,
            "discharge_date": today.isoformat(),
            "newborn_gender": "Female",
            "newborn_name": "Yazhini",
            "risk_flags": ["hypertension"],
        },
        headers=doctor,
    )
    assert created.status_code == 201, created.text
    patient_id = created.json()["patient"]["patient_id"]
    visits = created.json()["active_plan"]["visits"]
    assert [v["due_date"] for v in visits] == [v["due_date"] for v in preview["visits"]]
    first_visit = visits[0]
    assert first_visit["visit_type"] == "24h Checkup" and first_visit["status"] == "due_today"

    # 2. Coordinator sees her on the worklist (due today) alongside the late mothers.
    coordinator = _quick(client, "Coordinator")
    worklist = client.get("/api/v1/worklist", headers=coordinator).json()
    assert worklist["summary"]["due_today"] == 3
    assert "Revathi Subramanian" in {i["patient_name"] for i in worklist["items"]}

    # 3. Adds her husband with consent, previews the Tamil reminder, runs the daily job.
    member = client.post(
        f"/api/v1/patients/{patient_id}/family-members",
        json={
            "name": "Senthil Subramanian",
            "relation": "Husband",
            "contact_number": "9820055502",
            "consent_given": True,
        },
        headers=coordinator,
    )
    assert member.status_code == 201
    preview_msg = client.get(f"/api/v1/visits/{first_visit['visit_id']}/message-preview", headers=coordinator).json()
    assert preview_msg["message_text"].startswith("வணக்கம் Revathi Subramanian")
    run = client.post("/api/v1/admin/scheduler/run", headers=coordinator).json()
    assert run["batch_nudges_sent"] == 7  # 5 seeded + Revathi and her husband

    # 4. Kavya (top of the list) is reached and seen; she drops off the worklist.
    top = worklist["items"][0]
    assert top["patient_name"] == "Kavya Iyer"
    done = client.post(
        f"/api/v1/visits/{top['visit_id']}/complete",
        json={"completed_date": today.isoformat(), "note": "Came to OPD after the phone call"},
        headers=coordinator,
    )
    assert done.status_code == 200
    after = client.get("/api/v1/worklist", headers=coordinator).json()
    assert "Kavya Iyer" not in {i["patient_name"] for i in after["items"]}
    assert after["summary"]["overdue"] == 4

    # 5. The patient page shows reminders and the full audit trail.
    detail = client.get(f"/api/v1/patients/{patient_id}", headers=coordinator).json()
    assert {n["recipient_type"] for n in detail["nudges"]} == {"mother", "family"}
    trail = client.get(f"/api/v1/audit-log/patients/{patient_id}", headers=coordinator).json()
    assert [e["action"] for e in reversed(trail)][:3] == [
        "CREATE_DISCHARGE_PLAN",
        "ADD_FAMILY_CONSENT",
        "TRIGGER_NUDGE",
    ]

    # 6. Admin sees the outcome in the report and exports it anonymised.
    admin = _quick(client, "Admin")
    report = client.get("/api/v1/reports/outcomes", headers=admin).json()
    assert report["total_patients"] == 11
    csv_export = client.get("/api/v1/reports/outcomes", params={"export": "csv", "anonymize": True}, headers=admin)
    assert "Revathi" not in csv_export.text
