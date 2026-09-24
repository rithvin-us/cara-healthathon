from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import NudgeLog
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])

@router.post("/twilio/status")
def twilio_delivery_webhook(
    MessageSid: str = Form(None),
    MessageStatus: str = Form("delivered"),
    To: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    FR-013: Twilio Delivery-Status Webhook Handling. Records sent/delivered/failed status.
    """
    if To:
        nudge = db.query(NudgeLog).filter(NudgeLog.recipient_contact == To).order_by(NudgeLog.sent_at.desc()).first()
        if nudge:
            nudge.status = MessageStatus
            db.commit()
            return {"status": "success", "updated_nudge_id": nudge.nudge_id, "new_status": MessageStatus}

    return {"status": "received"}
