from datetime import date, timedelta, datetime
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.models import PostnatalVisit, DischargePlan, RiskFlag, VisitStatus, AuditLog

class CalendarEngine:
    @staticmethod
    def generate_default_visits(delivery_date: date) -> List[Tuple[str, date]]:
        """
        WHO-defined postnatal visit schedule (24h, 48-72h, 7-14d, 6wk)
        """
        return [
            ("24h Checkup", delivery_date + timedelta(days=1)),
            ("48-72h Checkup", delivery_date + timedelta(days=3)),
            ("7-14d Checkup", delivery_date + timedelta(days=10)),
            ("6wk Checkup", delivery_date + timedelta(days=42)),
        ]

    @staticmethod
    def generate_risk_visits(delivery_date: date, risk_flags: List[str]) -> List[Tuple[str, date]]:
        """
        FOGSI risk-based interval overrides (weekly cadence for high risk).
        """
        if not risk_flags:
            return []

        # If hypertension or hemorrhage history flagged, create weekly follow-up visits
        visits = []
        if "hypertension" in risk_flags or "hemorrhage_history" in risk_flags:
            visits = [
                ("Weekly Risk Checkup (Week 1)", delivery_date + timedelta(days=7)),
                ("Weekly Risk Checkup (Week 2)", delivery_date + timedelta(days=14)),
                ("Weekly Risk Checkup (Week 3)", delivery_date + timedelta(days=21)),
                ("Weekly Risk Checkup (Week 4)", delivery_date + timedelta(days=28)),
            ]
        elif "anemia" in risk_flags or "c_section" in risk_flags:
            visits = [
                ("Post-op/Anemia Checkup (Week 2)", delivery_date + timedelta(days=14)),
                ("Post-op/Anemia Checkup (Week 4)", delivery_date + timedelta(days=28)),
            ]
        else:
            visits = [
                ("Specialist Follow-Up", delivery_date + timedelta(days=14)),
            ]
        return visits

    @staticmethod
    def create_plan_visits(db: Session, plan_id: int, delivery_date: date, risk_flags: List[str]) -> List[PostnatalVisit]:
        """
        Creates visit entries for a discharge plan. If risk flags exist, uses risk cadence.
        """
        visit_schedule = []
        if risk_flags:
            # Risk override schedule takes priority or augments
            risk_visits = CalendarEngine.generate_risk_visits(delivery_date, risk_flags)
            default_visits = CalendarEngine.generate_default_visits(delivery_date)
            # Combine without duplicating exact dates
            existing_dates = set()
            for v_type, v_date in risk_visits:
                visit_schedule.append((v_type, v_date))
                existing_dates.add(v_date)
            for v_type, v_date in default_visits:
                if v_date not in existing_dates:
                    visit_schedule.append((v_type, v_date))
                    existing_dates.add(v_date)
        else:
            visit_schedule = CalendarEngine.generate_default_visits(delivery_date)

        created_visits = []
        for visit_type, due_date in visit_schedule:
            # compute initial status based on today
            today = date.today()
            if due_date < today:
                status = VisitStatus.OVERDUE.value
            elif due_date == today:
                status = VisitStatus.DUE_TODAY.value
            else:
                status = VisitStatus.UPCOMING.value

            visit = PostnatalVisit(
                plan_id=plan_id,
                visit_type=visit_type,
                due_date=due_date,
                status=status
            )
            db.add(visit)
            created_visits.append(visit)

        db.commit()
        for v in created_visits:
            db.refresh(v)
        return created_visits

    @staticmethod
    def recompute_all_visit_statuses(db: Session, current_date: date = None) -> int:
        """
        FR-005: Daily job computes each visit's status as Upcoming, Due Today, Overdue, or Completed/Missed.
        Returns number of visits updated.
        """
        if current_date is None:
            current_date = date.today()

        active_visits = db.query(PostnatalVisit).join(DischargePlan).filter(
            DischargePlan.status == "active",
            PostnatalVisit.status.in_([VisitStatus.UPCOMING.value, VisitStatus.DUE_TODAY.value, VisitStatus.OVERDUE.value])
        ).all()

        updated_count = 0
        for visit in active_visits:
            old_status = visit.status
            if visit.due_date < current_date:
                new_status = VisitStatus.OVERDUE.value
            elif visit.due_date == current_date:
                new_status = VisitStatus.DUE_TODAY.value
            else:
                new_status = VisitStatus.UPCOMING.value

            if old_status != new_status:
                visit.status = new_status
                updated_count += 1

        if updated_count > 0:
            db.commit()

            # Create audit entry
            audit = AuditLog(
                actor_id=0, # system job
                action="RECOMPUTE_VISIT_STATUSES",
                entity="PostnatalVisit",
                entity_id=None,
                details=f"Updated status for {updated_count} visits for date {current_date.isoformat()}"
            )
            db.add(audit)
            db.commit()

        return updated_count
