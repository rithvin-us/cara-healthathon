import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.models import Facility, StaffUser, Patient, DischargePlan, PostnatalVisit, FamilyMember, ConsentRecord, VisitStatus, AuditLog, NudgeLog
from app.core.security import get_password_hash, create_access_token
from app.services.calendar_engine import CalendarEngine
from app.services.content_filter import ContentFilter
from app.services.nudge_engine import NudgeEngine

# Setup isolated test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cara.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_test_environment():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed facility & users
    fac = Facility(name="Test City Hospital", address="123 Test St")
    db.add(fac)
    db.commit()
    db.refresh(fac)

    doc = StaffUser(
        facility_id=fac.facility_id,
        name="Dr. Test",
        role="Doctor",
        email="doctor@test.com",
        password_hash=get_password_hash("doc123")
    )
    coord = StaffUser(
        facility_id=fac.facility_id,
        name="Nurse Test",
        role="Coordinator",
        email="coord@test.com",
        password_hash=get_password_hash("coord123")
    )
    admin = StaffUser(
        facility_id=fac.facility_id,
        name="Admin Test",
        role="Admin",
        email="admin@test.com",
        password_hash=get_password_hash("admin123")
    )
    db.add_all([doc, coord, admin])
    db.commit()
    db.refresh(doc)
    db.refresh(coord)
    db.refresh(admin)

    doc_token = create_access_token({"sub": doc.email, "user_id": doc.user_id, "role": doc.role, "facility_id": fac.facility_id})
    coord_token = create_access_token({"sub": coord.email, "user_id": coord.user_id, "role": coord.role, "facility_id": fac.facility_id})
    admin_token = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": admin.role, "facility_id": fac.facility_id})

    db.close()
    return {
        "doc_token": doc_token,
        "coord_token": coord_token,
        "admin_token": admin_token,
        "facility_id": fac.facility_id
    }

client = TestClient(app)

# TC-01: Create Discharge Plan (FR-001)
def test_tc01_create_discharge_plan(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['doc_token']}"}
    today = date.today()
    payload = {
        "name": "Pooja Sharma",
        "contact_number": "+919988776655",
        "preferred_language": "English",
        "delivery_date": (today - timedelta(days=2)).isoformat(),
        "discharge_date": today.isoformat(),
        "newborn_gender": "Female",
        "newborn_name": "Baby Sharma",
        "risk_flags": []
    }
    response = client.post("/api/v1/patients", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["patient"]["name"] == "Pooja Sharma"
    assert data["active_plan"] is not None
    # Verify 4 default WHO visits generated
    visits = data["active_plan"]["visits"]
    assert len(visits) == 4
    visit_types = [v["visit_type"] for v in visits]
    assert "24h Checkup" in visit_types
    assert "48-72h Checkup" in visit_types
    assert "7-14d Checkup" in visit_types
    assert "6wk Checkup" in visit_types

# TC-02: Risk-based interval override (FR-002)
def test_tc02_apply_hypertension_risk_flag(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['doc_token']}"}
    today = date.today()
    payload = {
        "name": "Kavita Verma",
        "contact_number": "+919876500112",
        "preferred_language": "Hindi",
        "delivery_date": today.isoformat(),
        "discharge_date": today.isoformat(),
        "risk_flags": ["hypertension"]
    }
    response = client.post("/api/v1/patients", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    visits = data["active_plan"]["visits"]
    visit_types = [v["visit_type"] for v in visits]
    # Check that weekly risk checkups were applied
    assert any("Weekly Risk Checkup" in vt for vt in visit_types)

# TC-03: Compute visit status (FR-005)
def test_tc03_compute_visit_status(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['admin_token']}"}
    db = TestingSessionLocal()
    # Trigger scheduler recomputation
    response = client.post("/api/v1/admin/scheduler/run", headers=headers)
    assert response.status_code == 200
    db.close()

# TC-04: Mark visit complete (FR-006)
def test_tc04_mark_visit_complete(setup_test_environment):
    coord_headers = {"Authorization": f"Bearer {setup_test_environment['coord_token']}"}
    db = TestingSessionLocal()
    visit = db.query(PostnatalVisit).first()

    payload = {
        "completed_date": date.today().isoformat(),
        "note": "Home visit conducted, non-clinical check completed"
    }
    response = client.post(f"/api/v1/visits/{visit.visit_id}/complete", json=payload, headers=coord_headers)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "completed"
    assert res["audit_id"] is not None

    # Check audit log entry exists
    audit = db.query(AuditLog).filter(AuditLog.entity_id == visit.visit_id).first()
    assert audit is not None
    db.close()

# TC-05: Load ranked worklist (FR-008)
def test_tc05_load_ranked_worklist(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['coord_token']}"}
    response = client.get("/api/v1/worklist", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)

# TC-06: Nudge trigger on overdue visit (FR-011)
def test_tc06_trigger_nudge(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['coord_token']}"}
    db = TestingSessionLocal()
    visit = db.query(PostnatalVisit).filter(PostnatalVisit.status != "completed").first()
    
    response = client.post(f"/api/v1/visits/{visit.visit_id}/nudge", headers=headers)
    assert response.status_code == 200
    nudges = response.json()
    assert len(nudges) > 0
    assert nudges[0]["message_text"] is not None
    db.close()

# TC-07: Add family member with consent (FR-016)
def test_tc07_add_family_member_with_consent(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['coord_token']}"}
    db = TestingSessionLocal()
    patient = db.query(Patient).first()

    payload = {
        "name": "Rajesh Sharma",
        "relation": "Father",
        "contact_number": "+919988112233",
        "preferred_language": "English",
        "consent_given": True
    }
    response = client.post(f"/api/v1/patients/{patient.patient_id}/family-members", json=payload, headers=headers)
    assert response.status_code == 201
    fm_data = response.json()
    assert fm_data["name"] == "Rajesh Sharma"
    assert fm_data["latest_consent"] is True
    db.close()

# TC-08: Revoke consent mid-cycle (FR-017)
def test_tc08_revoke_consent(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['coord_token']}"}
    db = TestingSessionLocal()
    fm = db.query(FamilyMember).first()

    payload = {"consent_given": False}
    response = client.patch(f"/api/v1/family-members/{fm.family_id}/consent", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["latest_consent"] is False

    # Check that nudge engine blocks family nudge when consent is False
    is_active = NudgeEngine.is_family_consent_active(db, fm.family_id)
    assert is_active is False
    db.close()

# TC-09: Generate outcomes report (FR-019)
def test_tc09_generate_outcomes_report(setup_test_environment):
    headers = {"Authorization": f"Bearer {setup_test_environment['admin_token']}"}
    response = client.get("/api/v1/reports/outcomes", headers=headers)
    assert response.status_code == 200
    report = response.json()
    assert "overall_completion_rate_pct" in report
    assert "outcomes_by_visit_type" in report

# TC-10: Content filter rejects disallowed clinical terms (ERR-06 / AI-006)
def test_tc10_content_filter_clinical_rejection():
    bad_llm_output = "Mother should take 500mg dosage medicine for infection treatment."
    is_valid, reason = ContentFilter.inspect_text(bad_llm_output)
    assert is_valid is False
    assert "Disallowed clinical term" in reason

    # Test template fallback
    final_text, used_fallback = ContentFilter.filter_and_fallback_nudge(
        generated_text=bad_llm_output,
        mother_name="Pooja",
        visit_type="24h Checkup",
        due_date="Sep 25, 2026",
        facility_name="City Hospital"
    )
    assert used_fallback is True
    assert "dosage" not in final_text
    assert "Pooja" in final_text
    assert "24h Checkup" in final_text
