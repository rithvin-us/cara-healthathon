from datetime import timedelta

import pytest
from conftest import patient_named

from app.core.clock import facility_today


def _payload(**overrides):
    today = facility_today()
    data = {
        "name": "Nandini Reddy",
        "contact_number": "9820099001",
        "preferred_language": "Telugu",
        "delivery_date": (today - timedelta(days=1)).isoformat(),
        "discharge_date": today.isoformat(),
        "risk_flags": [],
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize(
    "flags,tier,count",
    [
        ([], "standard", 4),
        (["anemia"], "moderate", 6),
        (["c_section", "anemia"], "moderate", 6),
        (["hemorrhage_history"], "high", 8),
        (["anemia", "hypertension"], "high", 8),  # most frequent cadence wins, never averaged
        (["other"], "specialist", 5),
    ],
)
def test_preview_matches_what_is_created(client, doctor, flags, tier, count):
    payload = _payload(risk_flags=flags)
    preview = client.post(
        "/api/v1/schedule/preview",
        json={"delivery_date": payload["delivery_date"], "risk_flags": flags},
        headers=doctor,
    ).json()
    assert preview["risk_tier"] == tier and len(preview["visits"]) == count

    created = client.post("/api/v1/patients", json=payload, headers=doctor)
    assert created.status_code == 201, created.text
    visits = created.json()["active_plan"]["visits"]
    assert [(v["visit_type"], v["due_date"]) for v in visits] == [
        (v["visit_type"], v["due_date"]) for v in preview["visits"]
    ]


def test_phone_is_normalised_to_e164(client, doctor):
    res = client.post("/api/v1/patients", json=_payload(contact_number="098200 99001"), headers=doctor)
    assert res.json()["patient"]["contact_number"] == "+919820099001"


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"delivery_date": (facility_today() + timedelta(days=1)).isoformat()}, "future"),
        ({"discharge_date": (facility_today() - timedelta(days=5)).isoformat()}, "before the delivery date"),
        ({"contact_number": "12345"}, "valid mobile number"),
        ({"preferred_language": "Klingon"}, "Language must be one of"),
        ({"risk_flags": ["vampire_bite"]}, "risk flags"),
        ({"name": " "}, "name"),
    ],
)
def test_invalid_discharge_input_is_rejected(client, doctor, overrides, message):
    res = client.post("/api/v1/patients", json=_payload(**overrides), headers=doctor)
    assert res.status_code == 422
    assert message in res.json()["detail"]


def test_duplicate_phone_number_is_rejected(client, doctor):
    res = client.post("/api/v1/patients", json=_payload(contact_number="+919820010103"), headers=doctor)
    assert res.status_code == 409
    assert "Sunita Rao" in res.json()["detail"]


def test_coordinator_cannot_create_discharge_plan(client, coordinator):
    assert client.post("/api/v1/patients", json=_payload(), headers=coordinator).status_code == 403


def test_adding_risk_flag_later_keeps_history(client, doctor, db):
    patient = patient_named(db, "Divya Menon")
    plan = patient.discharge_plans[-1]
    completed_before = {v.visit_id for v in plan.visits if v.status == "completed"}

    res = client.post(f"/api/v1/patients/{patient.patient_id}/risk-flags", json={"flag_type": "anemia"}, headers=doctor)
    assert res.status_code == 200, res.text
    visits = res.json()["visits"]
    assert {v["visit_id"] for v in visits if v["status"] == "completed"} == completed_before
    assert {"Post-op/Anemia Checkup (Week 2)", "Post-op/Anemia Checkup (Week 4)"} <= {v["visit_type"] for v in visits}

    again = client.post(
        f"/api/v1/patients/{patient.patient_id}/risk-flags", json={"flag_type": "anemia"}, headers=doctor
    )
    assert again.status_code == 409


def test_only_doctor_applies_risk_flags(client, coordinator, db):
    patient = patient_named(db, "Divya Menon")
    res = client.post(
        f"/api/v1/patients/{patient.patient_id}/risk-flags", json={"flag_type": "anemia"}, headers=coordinator
    )
    assert res.status_code == 403


def test_closing_plan_removes_mother_from_worklist(client, coordinator, db):
    patient = patient_named(db, "Kavya Iyer")
    res = client.post(
        f"/api/v1/patients/{patient.patient_id}/plan/close",
        json={"reason": "Care transferred to her hometown PHC"},
        headers=coordinator,
    )
    assert res.status_code == 200 and res.json()["status"] == "closed"
    names = {i["patient_name"] for i in client.get("/api/v1/worklist", headers=coordinator).json()["items"]}
    assert "Kavya Iyer" not in names

    again = client.post(
        f"/api/v1/patients/{patient.patient_id}/plan/close", json={"reason": "Again"}, headers=coordinator
    )
    assert again.status_code == 409


def test_patient_detail_includes_newborn_family_and_reminders(client, coordinator, db):
    patient = patient_named(db, "Sunita Rao")
    data = client.get(f"/api/v1/patients/{patient.patient_id}", headers=coordinator).json()
    assert data["newborns"][0]["name_or_initial"] == "Ishaan"
    assert data["family_members"][0]["latest_consent"] is True
    assert len(data["nudges"]) == 4  # due-today and overdue reminders, to her and her husband
    assert [v["due_date"] for v in data["active_plan"]["visits"]] == sorted(
        v["due_date"] for v in data["active_plan"]["visits"]
    )
