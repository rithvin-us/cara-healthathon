import base64
import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.models import NudgeLog

router = APIRouter(prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])
logger = logging.getLogger("cara.webhooks")

_KNOWN_STATUSES = {"queued", "sending", "sent", "delivered", "read", "failed", "undelivered"}


def _twilio_signature(url: str, params: dict[str, str], auth_token: str) -> str:
    payload = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


@router.post("/twilio/status")
async def twilio_delivery_webhook(request: Request, db: Session = Depends(get_db)):
    """FR-013: Twilio delivery-status callback. Requests are verified with the
    X-Twilio-Signature header whenever real Twilio sending is enabled."""
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}

    if settings.twilio_enabled:
        url = settings.TWILIO_STATUS_CALLBACK_URL or str(request.url)
        expected = _twilio_signature(url, params, settings.TWILIO_AUTH_TOKEN)
        if not hmac.compare_digest(expected, request.headers.get("X-Twilio-Signature", "")):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    sid = params.get("MessageSid")
    new_status = (params.get("MessageStatus") or "").lower()
    if not sid or new_status not in _KNOWN_STATUSES:
        return {"status": "ignored"}

    nudge = db.query(NudgeLog).filter(NudgeLog.provider_message_id == sid).first()
    if not nudge:
        logger.info("Status callback for unknown MessageSid %s", sid)
        return {"status": "unknown_message"}

    nudge.status = new_status
    db.commit()
    return {"status": "updated", "nudge_id": nudge.nudge_id, "new_status": new_status}
