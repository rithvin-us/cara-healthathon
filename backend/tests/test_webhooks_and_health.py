from conftest import open_visit

from app.core.config import settings
from app.models.models import NudgeLog
from app.routers.webhooks import _twilio_signature


def _seed_nudge(db):
    visit = open_visit(db, "Kavya Iyer", "6wk Checkup")
    return db.query(NudgeLog).filter_by(visit_id=visit.visit_id).first()


def test_status_callback_updates_by_message_sid(client, db):
    nudge = _seed_nudge(db)
    res = client.post(
        "/api/v1/webhooks/twilio/status", data={"MessageSid": nudge.provider_message_id, "MessageStatus": "failed"}
    )
    assert res.json() == {"status": "updated", "nudge_id": nudge.nudge_id, "new_status": "failed"}
    db.refresh(nudge)
    assert nudge.status == "failed"


def test_status_callback_ignores_unknown(client):
    assert client.post(
        "/api/v1/webhooks/twilio/status", data={"MessageSid": "SMnope", "MessageStatus": "sent"}
    ).json() == {"status": "unknown_message"}
    assert client.post("/api/v1/webhooks/twilio/status", data={"MessageStatus": "bogus"}).json() == {
        "status": "ignored"
    }


def test_signature_required_when_twilio_enabled(client, db, monkeypatch):
    monkeypatch.setattr(settings, "NUDGE_PROVIDER", "twilio")
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACtest")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "secret-token")
    monkeypatch.setattr(settings, "TWILIO_STATUS_CALLBACK_URL", "https://cara.example/api/v1/webhooks/twilio/status")
    nudge = _seed_nudge(db)
    params = {"MessageSid": nudge.provider_message_id, "MessageStatus": "delivered"}

    assert client.post("/api/v1/webhooks/twilio/status", data=params).status_code == 403
    signature = _twilio_signature(settings.TWILIO_STATUS_CALLBACK_URL, params, "secret-token")
    ok = client.post("/api/v1/webhooks/twilio/status", data=params, headers={"X-Twilio-Signature": signature})
    assert ok.status_code == 200 and ok.json()["status"] == "updated"


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["database"] == "ok" and body["nudge_provider"] == "simulated"


def test_validation_errors_are_readable(client, doctor):
    res = client.post("/api/v1/patients", json={"name": "X"}, headers=doctor)
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], str) and "contact number" in res.json()["detail"]


def test_responses_carry_request_id(client):
    assert client.get("/api/v1/health").headers.get("X-Request-ID")


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


def test_twilio_whatsapp_failure_falls_back_to_sms(client, coordinator, db, monkeypatch):
    from app.services import nudge_engine

    monkeypatch.setattr(settings, "NUDGE_PROVIDER", "twilio")
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACtest")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "secret-token")
    monkeypatch.setattr(settings, "TWILIO_SMS_NUMBER", "+15005550006")
    calls = []

    def fake_post(url, data, auth, timeout):
        calls.append(data)
        if data["To"].startswith("whatsapp:"):
            return _FakeResponse(400, {"message": "not opted in"})
        return _FakeResponse(201, {"sid": f"SM{len(calls):030d}", "status": "queued"})

    monkeypatch.setattr(nudge_engine.requests, "post", fake_post)
    visit = open_visit(db, "Meera Kapoor", "48-72h Checkup")
    nudges = client.post(f"/api/v1/visits/{visit.visit_id}/nudge", headers=coordinator).json()

    assert [n["channel"] for n in nudges] == ["sms", "sms"]  # Meera and her husband
    assert all(n["status"] == "queued" for n in nudges)
    assert calls[0]["To"] == "whatsapp:+919820010107" and calls[1]["To"] == "+919820010107"
