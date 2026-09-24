from sqlalchemy.orm import Session
from app.models.models import PostnatalVisit, VisitStatus, Facility
from app.services.content_filter import ContentFilter

class DigestService:
    @staticmethod
    def generate_weekly_digest(db: Session, facility_id: int) -> dict:
        facility = db.query(Facility).filter(Facility.facility_id == facility_id).first()
        facility_name = facility.name if facility else "Facility"

        overdue_count = db.query(PostnatalVisit).join(PostnatalVisit.plan).join(PostnatalVisit.plan.property.mapper.class_.patient).filter(
            PostnatalVisit.status == VisitStatus.OVERDUE.value
        ).count()

        due_today_count = db.query(PostnatalVisit).join(PostnatalVisit.plan).join(PostnatalVisit.plan.property.mapper.class_.patient).filter(
            PostnatalVisit.status == VisitStatus.DUE_TODAY.value
        ).count()

        raw_digest = f"Weekly summary for {facility_name}: {overdue_count} visits are currently overdue, and {due_today_count} visits are due today across your patient panel."
        final_digest, is_fallback = ContentFilter.filter_and_fallback_digest(raw_digest, facility_name, overdue_count)

        return {
            "facility_name": facility_name,
            "overdue_count": overdue_count,
            "due_today_count": due_today_count,
            "digest_text": final_digest,
            "is_fallback_used": is_fallback
        }
