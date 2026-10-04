"""Synthetic demo data.

Every date is relative to the facility's today, so the demo always opens on
the same picture: seven mothers due or late, a mix of risk flags, family
consent given and withdrawn, and a reminder history. All names and phone
numbers are made up. Never point NUDGE_PROVIDER=twilio at this data.

    python -m app.seed           # seed an empty database
    python -m app.seed --reset   # wipe and reseed
"""

import argparse
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta, timezone

from app.core.clock import facility_today
from app.core.config import settings
from app.core.security import get_password_hash
from app.database import Base, SessionLocal, engine
from app.models.models import (
    AuditLog,
    ConsentRecord,
    DischargePlan,
    Facility,
    FamilyMember,
    Newborn,
    NudgeLog,
    Patient,
    PostnatalVisit,
    RiskFlag,
    StaffUser,
    VisitStatus,
)
from app.services import calendar_engine, message_templates

IST = timezone(timedelta(hours=5, minutes=30))

DEMO_PASSWORDS = {
    "doctor@cara.health": "doctor123",
    "coordinator@cara.health": "coord123",
    "admin@cara.health": "admin123",
}


def _utc(day: date, hour: int = 9, minute: int = 0) -> datetime:
    """A facility-local (IST) wall-clock time on `day`, stored as naive UTC."""
    return datetime.combine(day, time(hour, minute), tzinfo=IST).astimezone(UTC).replace(tzinfo=None)


@dataclass
class Relative:
    name: str
    relation: str
    phone: str
    consent: bool = True
    revoked_days_ago: int | None = None


@dataclass
class DemoMother:
    name: str
    phone: str
    language: str
    delivered_days_ago: int
    risk_flags: list[str] = field(default_factory=list)
    baby_name: str | None = None
    baby_gender: str = "Female"
    completed: list[str] = field(default_factory=list)  # visit types done on their due date
    missed: dict[str, str] = field(default_factory=dict)  # visit type -> reason text
    notes: dict[str, str] = field(default_factory=dict)
    relatives: list[Relative] = field(default_factory=list)
    reminded: dict[str, list[str]] = field(default_factory=dict)  # visit type -> triggers already sent
    closed_reason: str | None = None


MOTHERS = [
    DemoMother(
        "Kavya Iyer",
        "+919820010101",
        "Tamil",
        48,
        baby_name="Aadhira",
        completed=["24h Checkup", "48-72h Checkup", "7-14d Checkup"],
        notes={"7-14d Checkup": "Seen at OPD with her mother"},
        reminded={"6wk Checkup": ["due_today", "overdue"]},
    ),
    DemoMother(
        "Fatima Shaikh",
        "+919820010102",
        "Hindi",
        32,
        ["anemia"],
        baby_name="Ayaan",
        baby_gender="Male",
        completed=["24h Checkup", "48-72h Checkup", "7-14d Checkup", "Post-op/Anemia Checkup (Week 2)"],
        relatives=[Relative("Zoya Shaikh", "Sister", "+919820020102", consent=True, revoked_days_ago=6)],
        reminded={"Post-op/Anemia Checkup (Week 4)": ["due_today", "overdue"]},
    ),
    DemoMother(
        "Sunita Rao",
        "+919820010103",
        "Hindi",
        17,
        ["hypertension"],
        baby_name="Ishaan",
        baby_gender="Male",
        completed=["24h Checkup", "48-72h Checkup", "Weekly Risk Checkup (Week 1)", "7-14d Checkup"],
        notes={"7-14d Checkup": "Home visit by ASHA worker"},
        relatives=[Relative("Ramesh Rao", "Husband", "+919820020103")],
        reminded={"Weekly Risk Checkup (Week 2)": ["due_today", "overdue"]},
    ),
    DemoMother(
        "Lakshmi Narayanan",
        "+919820010104",
        "Tamil",
        12,
        ["c_section"],
        completed=["24h Checkup", "48-72h Checkup"],
        relatives=[Relative("Saraswathi Narayanan", "Mother", "+919820020104")],
        reminded={"7-14d Checkup": ["due_today", "overdue"]},
    ),
    DemoMother(
        "Priyanka Deshmukh",
        "+919820010105",
        "Marathi",
        8,
        ["hemorrhage_history"],
        baby_name="Mira",
        completed=["24h Checkup", "48-72h Checkup"],
        relatives=[Relative("Sachin Deshmukh", "Husband", "+919820020105")],
        reminded={"Weekly Risk Checkup (Week 1)": ["due_today"]},
    ),
    DemoMother(
        "Anjali Patel",
        "+919820010106",
        "Gujarati",
        1,
        baby_gender="Male",
    ),
    DemoMother(
        "Meera Kapoor",
        "+919820010107",
        "English",
        3,
        baby_name="Siya",
        completed=["24h Checkup"],
        relatives=[Relative("Arjun Kapoor", "Husband", "+919820020107")],
    ),
    DemoMother(
        "Divya Menon",
        "+919820010108",
        "English",
        20,
        baby_name="Nila",
        completed=["24h Checkup", "48-72h Checkup", "7-14d Checkup"],
    ),
    DemoMother(
        "Shalini Murugan",
        "+919820010109",
        "Tamil",
        5,
        ["hypertension"],
        baby_gender="Male",
        completed=["24h Checkup"],
        missed={"48-72h Checkup": "couldn't be reached"},
    ),
    DemoMother(
        "Rekha Yadav",
        "+919820010110",
        "Hindi",
        50,
        baby_name="Anvi",
        completed=["24h Checkup", "7-14d Checkup", "6wk Checkup"],
        missed={"48-72h Checkup": "couldn't be reached"},
        closed_reason="Follow-up complete",
    ),
]


def _audit(
    db,
    at: datetime,
    action: str,
    entity: str,
    details: str,
    *,
    actor=None,
    facility_id,
    patient_id=None,
    entity_id=None,
):
    db.add(
        AuditLog(
            facility_id=facility_id,
            patient_id=patient_id,
            actor_id=actor.user_id if actor else 0,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details,
            timestamp=at,
        )
    )


def _seed(db) -> dict:
    today = facility_today()

    facility = Facility(name="City Maternity & Children's Hospital", address="Andheri East, Mumbai, Maharashtra")
    db.add(facility)
    db.flush()

    def staff(name, role, email, password, active=True):
        user = StaffUser(
            facility_id=facility.facility_id,
            name=name,
            role=role,
            email=email,
            password_hash=get_password_hash(password),
            is_active=active,
        )
        db.add(user)
        return user

    doctor = staff("Dr. Ananya Sharma", "Doctor", "doctor@cara.health", DEMO_PASSWORDS["doctor@cara.health"])
    coordinator = staff(
        "Priya Patel", "Coordinator", "coordinator@cara.health", DEMO_PASSWORDS["coordinator@cara.health"]
    )
    admin = staff("Rajesh Kumar", "Admin", "admin@cara.health", DEMO_PASSWORDS["admin@cara.health"])
    staff("Kavitha Raman", "Coordinator", "kavitha.raman@cara.health", "kavitha-demo-2026")
    staff("Dr. Vikram Joshi", "Doctor", "vikram.joshi@cara.health", "vikram-demo-2026", active=False)
    db.flush()

    for m in MOTHERS:
        delivered = today - timedelta(days=m.delivered_days_ago)
        discharged = min(delivered + timedelta(days=2 if "c_section" in m.risk_flags else 1), today)

        patient = Patient(
            facility_id=facility.facility_id,
            name=m.name,
            contact_number=m.phone,
            preferred_language=m.language,
            delivery_date=delivered,
            discharge_date=discharged,
            created_at=_utc(discharged, 11),
        )
        patient.newborns.append(Newborn(dob=delivered, gender=m.baby_gender, name_or_initial=m.baby_name))
        plan = DischargePlan(created_by=doctor.user_id, created_at=_utc(discharged, 11))
        plan.risk_flags = [RiskFlag(flag_type=f, applied_at=_utc(discharged, 11)) for f in m.risk_flags]
        patient.discharge_plans.append(plan)
        db.add(patient)
        db.flush()

        calendar_engine.create_plan_visits(db, plan, delivered, m.risk_flags, today=today)
        _audit(
            db,
            _utc(discharged, 11),
            "CREATE_DISCHARGE_PLAN",
            "DischargePlan",
            f"Discharge plan for {m.name} with {len(plan.visits)} visits"
            + (f"; risk: {message_templates.describe_risks(m.risk_flags)}" if m.risk_flags else ""),
            actor=doctor,
            facility_id=facility.facility_id,
            patient_id=patient.patient_id,
            entity_id=plan.plan_id,
        )

        visits = {v.visit_type: v for v in plan.visits}
        for visit_type in m.completed:
            v = visits[visit_type]
            v.status = VisitStatus.COMPLETED.value
            v.completed_date = v.due_date
            v.note = m.notes.get(visit_type)
            _audit(
                db,
                _utc(v.due_date, 15),
                "MARK_VISIT_COMPLETE",
                "PostnatalVisit",
                f"{message_templates.describe_visit(visit_type)} marked done on {message_templates.format_date(v.due_date, 'English')}",
                actor=coordinator,
                facility_id=facility.facility_id,
                patient_id=patient.patient_id,
                entity_id=v.visit_id,
            )
        for visit_type, reason in m.missed.items():
            v = visits[visit_type]
            v.status = VisitStatus.MISSED.value
            v.note = f"Missed: {reason}"
            _audit(
                db,
                _utc(v.due_date + timedelta(days=1), 16),
                "MARK_VISIT_MISSED",
                "PostnatalVisit",
                f"{message_templates.describe_visit(visit_type)} marked missed: she {reason}",
                actor=coordinator,
                facility_id=facility.facility_id,
                patient_id=patient.patient_id,
                entity_id=v.visit_id,
            )

        members = []
        for r in m.relatives:
            member = FamilyMember(
                patient_id=patient.patient_id,
                name=r.name,
                relation=r.relation,
                contact_number=r.phone,
                preferred_language=m.language,
            )
            db.add(member)
            db.flush()
            db.add(
                ConsentRecord(
                    family_id=member.family_id,
                    consent_given=r.consent,
                    recorded_by=coordinator.user_id,
                    timestamp=_utc(discharged, 12),
                )
            )
            _audit(
                db,
                _utc(discharged, 12),
                "ADD_FAMILY_CONSENT",
                "FamilyMember",
                f"Added {r.name} ({r.relation}); consent given",
                actor=coordinator,
                facility_id=facility.facility_id,
                patient_id=patient.patient_id,
                entity_id=member.family_id,
            )
            if r.revoked_days_ago is not None:
                revoked_at = _utc(today - timedelta(days=r.revoked_days_ago), 10, 30)
                db.add(
                    ConsentRecord(
                        family_id=member.family_id,
                        consent_given=False,
                        recorded_by=coordinator.user_id,
                        timestamp=revoked_at,
                    )
                )
                _audit(
                    db,
                    revoked_at,
                    "REVOKE_CONSENT",
                    "ConsentRecord",
                    f"Consent withdrawn for {r.name} ({r.relation})",
                    actor=coordinator,
                    facility_id=facility.facility_id,
                    patient_id=patient.patient_id,
                )
            else:
                members.append(member)

        for visit_type, triggers in m.reminded.items():
            v = visits[visit_type]
            for trigger in triggers:
                sent_day = v.due_date if trigger == "due_today" else v.due_date + timedelta(days=1)
                sent_at = _utc(sent_day, 9, 5)
                kind = "mother_due" if trigger == "due_today" else "mother_overdue"
                rows = [
                    (
                        "mother",
                        m.phone,
                        message_templates.render(
                            kind,
                            m.language,
                            name=m.name,
                            facility=facility.name,
                            visit_type=v.visit_type,
                            due_date=v.due_date,
                        ),
                    )
                ]
                for member in members:
                    rows.append(
                        (
                            "family",
                            member.contact_number,
                            message_templates.render(
                                "family" if trigger == "due_today" else "family_overdue",
                                member.preferred_language,
                                name=member.name,
                                facility=facility.name,
                                visit_type=v.visit_type,
                                due_date=v.due_date,
                                mother=m.name,
                            ),
                        )
                    )
                for recipient_type, contact, text in rows:
                    db.add(
                        NudgeLog(
                            visit_id=v.visit_id,
                            channel="whatsapp",
                            recipient_type=recipient_type,
                            recipient_contact=contact,
                            sent_at=sent_at,
                            status="delivered" if trigger == "due_today" else "read",
                            message_text=text,
                            provider_message_id=f"SIMSEED{v.visit_id}{trigger[:3]}{recipient_type[:1]}",
                            trigger=trigger,
                        )
                    )
                _audit(
                    db,
                    sent_at,
                    "TRIGGER_NUDGE",
                    "PostnatalVisit",
                    f"{'Due-day' if trigger == 'due_today' else 'Late'} reminder for {message_templates.describe_visit(v.visit_type)}: {len(rows)} of {len(rows)} messages sent",
                    facility_id=facility.facility_id,
                    patient_id=patient.patient_id,
                    entity_id=v.visit_id,
                )

        if m.closed_reason:
            plan.status = "closed"
            plan.closed_at = _utc(today - timedelta(days=2), 17)
            plan.closed_reason = m.closed_reason
            _audit(
                db,
                plan.closed_at,
                "CLOSE_DISCHARGE_PLAN",
                "DischargePlan",
                f"Plan closed: {m.closed_reason}",
                actor=coordinator,
                facility_id=facility.facility_id,
                patient_id=patient.patient_id,
                entity_id=plan.plan_id,
            )

    db.flush()
    calendar_engine.recompute_all_visit_statuses(db, today)
    db.commit()
    return {
        "facility": facility.name,
        "staff": db.query(StaffUser).count(),
        "patients": db.query(Patient).count(),
        "visits": db.query(PostnatalVisit).count(),
        "as_of": today.isoformat(),
        "admin_user_id": admin.user_id,
    }


def seed_database() -> dict | None:
    """Seeds an empty database. Returns None if data already exists."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Facility).first():
            return None
        return _seed(db)
    finally:
        db.close()


def reset_and_seed() -> dict:
    """Drops every table, recreates the schema and loads the demo data."""
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        return _seed(db)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Cara's synthetic demo data.")
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding")
    args = parser.parse_args()

    if args.reset:
        summary = reset_and_seed()
    else:
        summary = seed_database()
        if summary is None:
            print("Database already has data. Use --reset to start over.")
            return

    print(
        f"Seeded {summary['patients']} mothers and {summary['visits']} visits at {summary['facility']} "
        f"(as of {summary['as_of']}, database {settings.DATABASE_URL.split('://')[0]})."
    )
    print("Demo sign-in:")
    for email, password in DEMO_PASSWORDS.items():
        print(f"  {email:<26} {password}")


if __name__ == "__main__":
    main()
