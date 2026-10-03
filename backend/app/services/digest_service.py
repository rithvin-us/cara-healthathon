from sqlalchemy.orm import Session

from app.models.models import DischargePlan, DischargePlanStatus, Facility, Patient, PostnatalVisit, VisitStatus
from app.services.content_filter import ContentFilter


class DigestService:
    @staticmethod
    def _count(db: Session, facility_id: int, status: str) -> int:
        return (
            db.query(PostnatalVisit)
            .join(DischargePlan)
            .join(Patient, DischargePlan.patient_id == Patient.patient_id)
            .filter(
                Patient.facility_id == facility_id,
                DischargePlan.status == DischargePlanStatus.ACTIVE.value,
                PostnatalVisit.status == status,
            )
            .count()
        )

    @staticmethod
    def generate_weekly_digest(db: Session, facility_id: int) -> dict:
        """FR-012: plain-language weekly summary for the coordinator's panel."""
        facility = db.get(Facility, facility_id)
        facility_name = facility.name if facility else "your facility"

        overdue = DigestService._count(db, facility_id, VisitStatus.OVERDUE.value)
        due_today = DigestService._count(db, facility_id, VisitStatus.DUE_TODAY.value)

        if overdue == 0 and due_today == 0:
            raw = f"Weekly summary for {facility_name}: every mother is up to date with her checkups."
        else:
            raw = (
                f"Weekly summary for {facility_name}: {overdue} "
                f"{'visit is' if overdue == 1 else 'visits are'} overdue and {due_today} "
                f"{'is' if due_today == 1 else 'are'} due today. "
                "Start with the mothers at the top of the follow-up list."
            )
        text, is_fallback = ContentFilter.filter_and_fallback_digest(raw, facility_name, overdue)
        return {
            "facility_name": facility_name,
            "overdue_count": overdue,
            "due_today_count": due_today,
            "digest_text": text,
            "is_fallback_used": is_fallback,
        }
