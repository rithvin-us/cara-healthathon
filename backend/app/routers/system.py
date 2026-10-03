import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.clock import facility_today
from app.core.config import settings
from app.database import get_db
from app.models.models import Facility
from app.routers.admin import run_daily_job
from app.schemas.schemas import HealthOut

router = APIRouter(prefix=settings.API_V1_STR, tags=["system"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    """Liveness + database check, for uptime monitors and the deploy smoke test."""
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 - report, don't crash the health check
        database = "unavailable"
    return HealthOut(
        status="ok" if database == "ok" else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=database,
        demo_mode=settings.DEMO_MODE,
        nudge_provider="twilio" if settings.twilio_enabled else "simulated",
    )


@router.get("/internal/cron/daily", include_in_schema=False)
def daily_cron(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    """Daily job for every facility. Vercel Cron calls this with
    `Authorization: Bearer $CRON_SECRET`; without a configured secret it is disabled."""
    if not settings.CRON_SECRET or not hmac.compare_digest(authorization, f"Bearer {settings.CRON_SECRET}"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    today = facility_today()
    results = [run_daily_job(db, today, f.facility_id, actor=None) for f in db.query(Facility).all()]
    return {
        "status": "completed",
        "run_date": today,
        "facilities": len(results),
        "visits_status_updated": sum(r.visits_status_updated for r in results),
        "batch_nudges_sent": sum(r.batch_nudges_sent for r in results),
    }
