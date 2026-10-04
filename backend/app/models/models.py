import enum

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, event
from sqlalchemy.orm import relationship

from app.core.clock import utcnow
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


OPEN_VISIT_STATUSES = (VisitStatus.UPCOMING.value, VisitStatus.DUE_TODAY.value, VisitStatus.OVERDUE.value)
CLOSED_VISIT_STATUSES = (VisitStatus.COMPLETED.value, VisitStatus.MISSED.value)


class DischargePlanStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class RiskFlagType(str, enum.Enum):
    HYPERTENSION = "hypertension"
    HEMORRHAGE_HISTORY = "hemorrhage_history"
    ANEMIA = "anemia"
    C_SECTION = "c_section"
    OTHER = "other"


class MissedReason(str, enum.Enum):
    UNREACHABLE = "unreachable"
    DECLINED = "declined"
    MOVED = "moved"


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
    facility_id = Column(Integer, ForeignKey("facility.facility_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # StaffRole value
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    facility = relationship("Facility", back_populates="staff_users")
    discharge_plans = relationship("DischargePlan", back_populates="creator")


class Patient(Base):
    __tablename__ = "patient"
    __table_args__ = (Index("ix_patient_facility_contact", "facility_id", "contact_number"),)

    patient_id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facility.facility_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    preferred_language = Column(String, default="English", nullable=False)
    delivery_date = Column(Date, nullable=False)
    discharge_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    facility = relationship("Facility", back_populates="patients")
    newborns = relationship("Newborn", back_populates="patient", cascade="all, delete-orphan")
    discharge_plans = relationship(
        "DischargePlan", back_populates="patient", cascade="all, delete-orphan", order_by="DischargePlan.plan_id"
    )
    family_members = relationship("FamilyMember", back_populates="patient", cascade="all, delete-orphan")


class Newborn(Base):
    __tablename__ = "newborn"

    newborn_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False, index=True)
    dob = Column(Date, nullable=False)
    gender = Column(String, nullable=True)
    name_or_initial = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="newborns")


class DischargePlan(Base):
    __tablename__ = "discharge_plan"

    plan_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("staff_user.user_id"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    status = Column(String, default=DischargePlanStatus.ACTIVE.value, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    closed_reason = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="discharge_plans")
    creator = relationship("StaffUser", back_populates="discharge_plans")
    risk_flags = relationship("RiskFlag", back_populates="plan", cascade="all, delete-orphan")
    visits = relationship(
        "PostnatalVisit", back_populates="plan", cascade="all, delete-orphan", order_by="PostnatalVisit.due_date"
    )


class RiskFlag(Base):
    __tablename__ = "risk_flag"

    flag_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("discharge_plan.plan_id"), nullable=False, index=True)
    flag_type = Column(String, nullable=False)  # RiskFlagType value
    applied_at = Column(DateTime, default=utcnow, nullable=False)

    plan = relationship("DischargePlan", back_populates="risk_flags")


class PostnatalVisit(Base):
    __tablename__ = "postnatal_visit"
    __table_args__ = (Index("ix_visit_status_due", "status", "due_date"),)

    visit_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("discharge_plan.plan_id"), nullable=False, index=True)
    visit_type = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, default=VisitStatus.UPCOMING.value, nullable=False)
    completed_date = Column(Date, nullable=True)
    note = Column(Text, nullable=True)

    plan = relationship("DischargePlan", back_populates="visits")
    nudges = relationship("NudgeLog", back_populates="visit", cascade="all, delete-orphan")


class FamilyMember(Base):
    __tablename__ = "family_member"

    family_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    preferred_language = Column(String, default="English", nullable=False)

    patient = relationship("Patient", back_populates="family_members")
    consent_records = relationship(
        "ConsentRecord",
        back_populates="family_member",
        cascade="all, delete-orphan",
        order_by="ConsentRecord.consent_id",
    )


class ConsentRecord(Base):
    __tablename__ = "consent_record"

    consent_id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("family_member.family_id"), nullable=False, index=True)
    consent_given = Column(Boolean, default=False, nullable=False)
    recorded_by = Column(Integer, ForeignKey("staff_user.user_id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)

    family_member = relationship("FamilyMember", back_populates="consent_records")


class NudgeLog(Base):
    __tablename__ = "nudge_log"

    nudge_id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("postnatal_visit.visit_id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # whatsapp | sms
    recipient_type = Column(String, nullable=False)  # mother | family
    recipient_contact = Column(String, nullable=False)
    sent_at = Column(DateTime, default=utcnow, nullable=False)
    status = Column(String, default="sent", nullable=False)  # queued | sent | delivered | read | failed | undelivered
    message_text = Column(Text, nullable=False)
    provider_message_id = Column(String, nullable=True, index=True)
    trigger = Column(String, default="scheduled", nullable=False)  # scheduled | manual

    visit = relationship("PostnatalVisit", back_populates="nudges")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facility.facility_id"), nullable=True, index=True)
    patient_id = Column(Integer, nullable=True, index=True)
    actor_id = Column(Integer, nullable=True)  # staff user_id, or 0 for the system scheduler
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    details = Column(Text, nullable=True)


class AuditLogImmutableError(RuntimeError):
    pass


@event.listens_for(AuditLog, "before_update")
def _block_audit_update(_mapper, _connection, _target):
    raise AuditLogImmutableError("Audit log entries are append-only and cannot be modified.")


@event.listens_for(AuditLog, "before_delete")
def _block_audit_delete(_mapper, _connection, _target):
    raise AuditLogImmutableError("Audit log entries are append-only and cannot be deleted.")
