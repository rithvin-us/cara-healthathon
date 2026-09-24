from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class StaffRole(str, enum.Enum):
    DOCTOR = "Doctor"
    COORDINATOR = "Coordinator"
    ADMIN = "Admin"

class VisitStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    DUE_TODAY = "due_today"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    MISSED = "missed"

class DischargePlanStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class Facility(Base):
    __tablename__ = "facility"

    facility_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)

    staff_users = relationship("StaffUser", back_populates="facility")
    patients = relationship("Patient", back_populates="facility")

class StaffUser(Base):
    __tablename__ = "staff_user"

    user_id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facility.facility_id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Doctor, Coordinator, Admin
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    facility = relationship("Facility", back_populates="staff_users")
    discharge_plans = relationship("DischargePlan", back_populates="creator")

class Patient(Base):
    __tablename__ = "patient"

    patient_id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facility.facility_id"), nullable=False)
    name = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    preferred_language = Column(String, default="English")
    delivery_date = Column(Date, nullable=False)
    discharge_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="patients")
    newborns = relationship("Newborn", back_populates="patient", cascade="all, delete-orphan")
    discharge_plans = relationship("DischargePlan", back_populates="patient", cascade="all, delete-orphan")
    family_members = relationship("FamilyMember", back_populates="patient", cascade="all, delete-orphan")

class Newborn(Base):
    __tablename__ = "newborn"

    newborn_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String, nullable=True)
    name_or_initial = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="newborns")

class DischargePlan(Base):
    __tablename__ = "discharge_plan"

    plan_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False)
    created_by = Column(Integer, ForeignKey("staff_user.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, closed

    patient = relationship("Patient", back_populates="discharge_plans")
    creator = relationship("StaffUser", back_populates="discharge_plans")
    risk_flags = relationship("RiskFlag", back_populates="plan", cascade="all, delete-orphan")
    visits = relationship("PostnatalVisit", back_populates="plan", cascade="all, delete-orphan")

class RiskFlag(Base):
    __tablename__ = "risk_flag"

    flag_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("discharge_plan.plan_id"), nullable=False)
    flag_type = Column(String, nullable=False) # e.g. hypertension, hemorrhage_history, anemia, c_section
    applied_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("DischargePlan", back_populates="risk_flags")

class PostnatalVisit(Base):
    __tablename__ = "postnatal_visit"

    visit_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("discharge_plan.plan_id"), nullable=False)
    visit_type = Column(String, nullable=False) # 24h, 48-72h, 7-14d, 6wk, risk_interval_w1, etc.
    due_date = Column(Date, nullable=False)
    status = Column(String, default="upcoming") # upcoming, due_today, overdue, completed, missed
    completed_date = Column(Date, nullable=True)
    note = Column(Text, nullable=True)

    plan = relationship("DischargePlan", back_populates="visits")
    nudges = relationship("NudgeLog", back_populates="visit", cascade="all, delete-orphan")

class FamilyMember(Base):
    __tablename__ = "family_member"

    family_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    preferred_language = Column(String, default="English")

    patient = relationship("Patient", back_populates="family_members")
    consent_records = relationship("ConsentRecord", back_populates="family_member", cascade="all, delete-orphan")

class ConsentRecord(Base):
    __tablename__ = "consent_record"

    consent_id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_member.family_id"), nullable=False)
    consent_given = Column(Boolean, default=False)
    recorded_by = Column(Integer, ForeignKey("staff_user.user_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    family_member = relationship("FamilyMember", back_populates="consent_records")

class NudgeLog(Base):
    __tablename__ = "nudge_log"

    nudge_id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("postnatal_visit.visit_id"), nullable=False)
    channel = Column(String, nullable=False) # whatsapp, sms
    recipient_type = Column(String, nullable=False) # mother, family
    recipient_contact = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="sent") # sent, delivered, failed
    message_text = Column(Text, nullable=False)

    visit = relationship("PostnatalVisit", back_populates="nudges")

class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True) # user_id or 0 for system
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
