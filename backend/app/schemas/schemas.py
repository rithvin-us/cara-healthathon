import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.models import MissedReason, RiskFlagType, StaffRole

SUPPORTED_LANGUAGES = ("English", "Hindi", "Tamil", "Marathi", "Gujarati", "Bengali", "Telugu", "Kannada")

_PHONE_DIGITS = re.compile(r"\D")


def normalise_phone(value: str) -> str:
    """Accept common Indian formats and return E.164 (+91XXXXXXXXXX)."""
    raw = (value or "").strip()
    has_plus = raw.startswith("+")
    digits = _PHONE_DIGITS.sub("", raw)
    if not has_plus:
        if len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]
        if len(digits) == 10:
            digits = "91" + digits
    if not 10 <= len(digits) <= 15:
        raise ValueError("Enter a valid mobile number, e.g. +91 98765 43210")
    return "+" + digits


class _Trimmed(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class QuickLoginRequest(BaseModel):
    role: StaffRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    role: str
    facility_id: int
    facility_name: str


class DemoAccount(BaseModel):
    role: str
    name: str
    email: str


class AuthConfigOut(BaseModel):
    demo_mode: bool
    facility_name: str | None = None
    demo_accounts: list[DemoAccount] = []


# --- Facility & staff ---
class FacilityOut(ORMModel):
    facility_id: int
    name: str
    address: str | None = None


class StaffUserCreate(_Trimmed):
    name: str = Field(min_length=2, max_length=120)
    role: StaffRole
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class StaffUserOut(ORMModel):
    user_id: int
    facility_id: int
    name: str
    role: str
    email: EmailStr
    is_active: bool


# --- Risk flags ---
class RiskFlagCreate(BaseModel):
    flag_type: RiskFlagType


class RiskFlagOut(ORMModel):
    flag_id: int
    plan_id: int
    flag_type: str
    applied_at: datetime


# --- Visits ---
class PostnatalVisitOut(ORMModel):
    visit_id: int
    plan_id: int
    visit_type: str
    due_date: date
    status: str
    completed_date: date | None = None
    note: str | None = None


class VisitCompleteRequest(_Trimmed):
    completed_date: date
    note: str | None = Field(default=None, max_length=500)


class VisitMissedRequest(BaseModel):
    reason: MissedReason


class VisitRescheduleRequest(BaseModel):
    due_date: date


class VisitActionOut(BaseModel):
    visit_id: int
    status: str
    due_date: date
    completed_date: date | None = None
    audit_id: int


class MessagePreviewOut(BaseModel):
    visit_id: int
    recipient_name: str
    recipient_contact: str
    language: str
    channel: str
    message_text: str
    provider: str


# --- Schedule preview ---
class SchedulePreviewRequest(BaseModel):
    delivery_date: date
    risk_flags: list[RiskFlagType] = []


class ScheduledVisit(BaseModel):
    visit_type: str
    due_date: date
    is_risk_visit: bool


class SchedulePreviewOut(BaseModel):
    risk_tier: str  # standard | moderate | high | specialist
    visits: list[ScheduledVisit]


# --- Patients & discharge plans ---
class PatientCreate(_Trimmed):
    name: str = Field(min_length=2, max_length=120)
    contact_number: str
    preferred_language: str = "English"
    delivery_date: date
    discharge_date: date
    newborn_gender: str | None = Field(default=None, max_length=20)
    newborn_name: str | None = Field(default=None, max_length=80)
    risk_flags: list[RiskFlagType] = []

    @field_validator("contact_number")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalise_phone(v)

    @field_validator("preferred_language")
    @classmethod
    def _language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(SUPPORTED_LANGUAGES)}")
        return v

    @field_validator("newborn_name", "newborn_gender")
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        return v or None


class PatientOut(ORMModel):
    patient_id: int
    facility_id: int
    name: str
    contact_number: str
    preferred_language: str
    delivery_date: date
    discharge_date: date
    created_at: datetime


class NewbornOut(ORMModel):
    newborn_id: int
    dob: date
    gender: str | None = None
    name_or_initial: str | None = None


class DischargePlanOut(ORMModel):
    plan_id: int
    patient_id: int
    created_by: int
    created_at: datetime
    status: str
    closed_at: datetime | None = None
    closed_reason: str | None = None
    risk_flags: list[RiskFlagOut] = []
    visits: list[PostnatalVisitOut] = []


class ClosePlanRequest(_Trimmed):
    reason: str = Field(min_length=3, max_length=200)


# --- Family & consent ---
class FamilyMemberCreate(_Trimmed):
    name: str = Field(min_length=2, max_length=120)
    relation: str = Field(min_length=2, max_length=40)
    contact_number: str
    preferred_language: str | None = None
    consent_given: bool = True

    @field_validator("contact_number")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalise_phone(v)


class FamilyMemberOut(BaseModel):
    family_id: int
    patient_id: int
    name: str
    relation: str
    contact_number: str
    preferred_language: str
    latest_consent: bool = False
    consent_updated_at: datetime | None = None


class ConsentUpdateRequest(BaseModel):
    consent_given: bool


# --- Nudges ---
class NudgeLogOut(ORMModel):
    nudge_id: int
    visit_id: int
    channel: str
    recipient_type: str
    recipient_contact: str
    sent_at: datetime
    status: str
    message_text: str
    trigger: str = "scheduled"


# --- Worklist & detail ---
class WorklistItem(BaseModel):
    patient_id: int
    patient_name: str
    contact_number: str
    preferred_language: str
    visit_id: int
    visit_type: str
    due_date: date
    days_overdue: int
    status: str
    risk_flags: list[str] = []
    last_reminder_at: datetime | None = None
    last_reminder_status: str | None = None


class WorklistSummary(BaseModel):
    overdue: int
    due_today: int
    high_risk: int
    upcoming_7_days: int


class WorklistOut(BaseModel):
    as_of: date
    summary: WorklistSummary
    items: list[WorklistItem]


class PatientDetailOut(BaseModel):
    patient: PatientOut
    newborns: list[NewbornOut] = []
    active_plan: DischargePlanOut | None = None
    family_members: list[FamilyMemberOut] = []
    nudges: list[NudgeLogOut] = []


# --- Audit ---
class AuditLogOut(ORMModel):
    audit_id: int
    actor_id: int | None = None
    actor_name: str | None = None
    patient_id: int | None = None
    action: str
    entity: str
    entity_id: int | None = None
    timestamp: datetime
    details: str | None = None


# --- Reports ---
class VisitTypeOutcome(BaseModel):
    visit_type: str
    total: int
    completed: int
    missed: int
    overdue: int
    completion_rate_pct: float


class OutcomesReportOut(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    total_patients: int
    total_visits: int
    completed_visits: int
    missed_visits: int
    overdue_visits: int
    overall_completion_rate_pct: float
    outcomes_by_visit_type: list[VisitTypeOutcome]


# --- Admin / scheduler ---
class SchedulerRunOut(BaseModel):
    status: str
    run_date: date
    visits_status_updated: int
    batch_nudges_sent: int


class DigestOut(BaseModel):
    facility_name: str
    overdue_count: int
    due_today_count: int
    digest_text: str
    is_fallback_used: bool


class HealthOut(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    demo_mode: bool
    nudge_provider: str
