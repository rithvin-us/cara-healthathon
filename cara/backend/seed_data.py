from datetime import date, timedelta
from app.database import SessionLocal, engine, Base
from app.models.models import Facility, StaffUser, Patient, Newborn, DischargePlan, RiskFlag, PostnatalVisit, FamilyMember, ConsentRecord, VisitStatus
from app.core.security import get_password_hash
from app.services.calendar_engine import CalendarEngine

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Facility).first():
            print("Database already seeded.")
            return

        print("Seeding database with initial facility, staff, and synthetic patient records...")

        # 1. Facility
        facility = Facility(
            name="City Maternity & Children's Hospital",
            address="100 Health Avenue, Mumbai, India"
        )
        db.add(facility)
        db.commit()
        db.refresh(facility)

        # 2. Staff Accounts
        doc = StaffUser(
            facility_id=facility.facility_id,
            name="Dr. Ananya Sharma (OBGYN)",
            role="Doctor",
            email="doctor@cara.health",
            password_hash=get_password_hash("doctor123")
        )
        coord = StaffUser(
            facility_id=facility.facility_id,
            name="Priya Patel (Lactation Counselor / Nurse)",
            role="Coordinator",
            email="coordinator@cara.health",
            password_hash=get_password_hash("coord123")
        )
        admin_user = StaffUser(
            facility_id=facility.facility_id,
            name="Rajesh Kumar (Facility Administrator)",
            role="Admin",
            email="admin@cara.health",
            password_hash=get_password_hash("admin123")
        )
        db.add_all([doc, coord, admin_user])
        db.commit()
        db.refresh(doc)
        db.refresh(coord)
        db.refresh(admin_user)

        # 3. Synthetic Patients
        today = date.today()

        # Patient 1: Overdue high-risk hypertension patient
        p1 = Patient(
            facility_id=facility.facility_id,
            name="Sunita Rao",
            contact_number="+919876543210",
            preferred_language="Hindi",
            delivery_date=today - timedelta(days=15),
            discharge_date=today - timedelta(days=13)
        )
        db.add(p1)
        db.commit()
        db.refresh(p1)

        plan1 = DischargePlan(
            patient_id=p1.patient_id,
            created_by=doc.user_id,
            status="active"
        )
        db.add(plan1)
        db.commit()
        db.refresh(plan1)

        rf1 = RiskFlag(plan_id=plan1.plan_id, flag_type="hypertension")
        db.add(rf1)
        db.commit()

        CalendarEngine.create_plan_visits(db, plan1.plan_id, p1.delivery_date, ["hypertension"])

        # Add family member for Sunita
        fm1 = FamilyMember(
            patient_id=p1.patient_id,
            name="Ramesh Rao",
            relation="Husband",
            contact_number="+919876543211",
            preferred_language="Hindi"
        )
        db.add(fm1)
        db.commit()
        db.refresh(fm1)

        cr1 = ConsentRecord(
            family_id=fm1.family_id,
            consent_given=True,
            recorded_by=coord.user_id
        )
        db.add(cr1)
        db.commit()

        # Patient 2: Normal 4-visit schedule, Due Today
        p2 = Patient(
            facility_id=facility.facility_id,
            name="Meera Kapoor",
            contact_number="+919812345678",
            preferred_language="English",
            delivery_date=today - timedelta(days=3),
            discharge_date=today - timedelta(days=1)
        )
        db.add(p2)
        db.commit()
        db.refresh(p2)

        plan2 = DischargePlan(
            patient_id=p2.patient_id,
            created_by=doc.user_id,
            status="active"
        )
        db.add(plan2)
        db.commit()
        db.refresh(plan2)

        CalendarEngine.create_plan_visits(db, plan2.plan_id, p2.delivery_date, [])

        # Recompute visit status to reflect overdue/due dates
        CalendarEngine.recompute_all_visit_statuses(db, today)

        print("Seeding completed successfully!")
        print("Default Accounts:")
        print("  Doctor:      doctor@cara.health / doctor123")
        print("  Coordinator: coordinator@cara.health / coord123")
        print("  Admin:       admin@cara.health / admin123")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
