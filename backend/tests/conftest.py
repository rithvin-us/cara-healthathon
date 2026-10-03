import os
import tempfile

# Point the app at a throwaway database before anything imports it.
_DB_DIR = tempfile.mkdtemp(prefix="cara-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_DB_DIR, 'test.db')}"
os.environ.setdefault("CARA_DEMO_MODE", "true")
os.environ.setdefault("CRON_SECRET", "test-cron-secret")

import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_real_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4, prefix=b"2b": _real_gensalt(rounds=4, prefix=prefix)  # fast hashes in tests

from app.core.config import settings  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.models import Facility, Patient, PostnatalVisit, StaffUser  # noqa: E402
from app.seed import DEMO_PASSWORDS, reset_and_seed  # noqa: E402

ROLE_EMAILS = {
    "Doctor": "doctor@cara.health",
    "Coordinator": "coordinator@cara.health",
    "Admin": "admin@cara.health",
}


@pytest.fixture(autouse=True)
def demo_data():
    """Every test starts from the same freshly seeded demo facility."""
    return reset_and_seed()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def login(client: TestClient, role: str) -> dict:
    email = ROLE_EMAILS[role]
    res = client.post("/api/v1/auth/login", json={"email": email, "password": DEMO_PASSWORDS[email]})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def doctor(client):
    return login(client, "Doctor")


@pytest.fixture
def coordinator(client):
    return login(client, "Coordinator")


@pytest.fixture
def admin(client):
    return login(client, "Admin")


@pytest.fixture
def other_facility(client, db):
    """A second hospital with its own coordinator, for tenancy-isolation tests."""
    facility = Facility(name="Other District Hospital", address="Pune")
    db.add(facility)
    db.flush()
    db.add(
        StaffUser(
            facility_id=facility.facility_id,
            name="Other Coordinator",
            role="Coordinator",
            email="other@cara.health",
            password_hash=get_password_hash("other-pass-123"),
        )
    )
    db.commit()
    res = client.post("/api/v1/auth/login", json={"email": "other@cara.health", "password": "other-pass-123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def patient_named(db, name: str) -> Patient:
    return db.query(Patient).filter(Patient.name == name).one()


def open_visit(db, patient_name: str, visit_type: str) -> PostnatalVisit:
    patient = patient_named(db, patient_name)
    return next(v for v in patient.discharge_plans[-1].visits if v.visit_type == visit_type)


@pytest.fixture
def demo_mode_off(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
