from datetime import timedelta

from app.core.security import create_access_token
from app.models.models import StaffUser


def test_login_rejects_wrong_password(client):
    res = client.post("/api/v1/auth/login", json={"email": "doctor@cara.health", "password": "not-the-password"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect email or password."


def test_login_rejects_unknown_email_with_same_message(client):
    res = client.post("/api/v1/auth/login", json={"email": "nobody@cara.health", "password": "whatever"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect email or password."


def test_login_succeeds_and_me_returns_user(client):
    res = client.post("/api/v1/auth/login", json={"email": "Doctor@Cara.Health", "password": "doctor123"})
    assert res.status_code == 200
    token = res.json()
    assert token["role"] == "Doctor" and token["facility_name"].startswith("City Maternity")
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.json()["email"] == "doctor@cara.health"


def test_inactive_account_cannot_sign_in(client):
    res = client.post("/api/v1/auth/login", json={"email": "vikram.joshi@cara.health", "password": "vikram-demo-2026"})
    assert res.status_code == 403


def test_deactivated_user_token_stops_working(client, admin, coordinator, db):
    coord = db.query(StaffUser).filter_by(email="coordinator@cara.health").one()
    assert client.get("/api/v1/worklist", headers=coordinator).status_code == 200
    client.patch(f"/api/v1/admin/staff/{coord.user_id}/toggle-active", headers=admin)
    assert client.get("/api/v1/worklist", headers=coordinator).status_code == 401


def test_expired_and_garbage_tokens_are_rejected(client, db):
    user = db.query(StaffUser).filter_by(email="doctor@cara.health").one()
    expired = create_access_token({"sub": user.email, "user_id": user.user_id}, expires_delta=timedelta(minutes=-1))
    for token in (expired, "not-a-jwt"):
        res = client.get("/api/v1/worklist", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_quick_login_in_demo_mode(client):
    config = client.get("/api/v1/auth/config").json()
    assert config["demo_mode"] is True
    assert [a["role"] for a in config["demo_accounts"]] == ["Doctor", "Coordinator", "Admin"]
    res = client.post("/api/v1/auth/quick-login", json={"role": "Coordinator"})
    assert res.status_code == 200 and res.json()["name"] == "Priya Patel"


def test_quick_login_rejects_unknown_role(client):
    assert client.post("/api/v1/auth/quick-login", json={"role": "Superuser"}).status_code == 422


def test_quick_login_disabled_outside_demo_mode(client, demo_mode_off):
    assert client.get("/api/v1/auth/config").json() == {"demo_mode": False, "facility_name": None, "demo_accounts": []}
    assert client.post("/api/v1/auth/quick-login", json={"role": "Admin"}).status_code == 404


def test_swagger_token_endpoint(client):
    res = client.post("/api/v1/auth/token", data={"username": "admin@cara.health", "password": "admin123"})
    assert res.status_code == 200 and res.json()["token_type"] == "bearer"
