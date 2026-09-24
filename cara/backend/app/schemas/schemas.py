from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date, datetime

# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    role: str
    facility_id: int

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    facility_id: Optional[int] = None

# Facility & Staff
class FacilityBase(BaseModel):
    name: str
    address: Optional[str] = None

class FacilityCreate(FacilityBase):
    pass

class FacilityOut(FacilityBase):
    facility_id: int
    class Config:
        from_attributes = True

class StaffUserCreate(BaseModel):
    name: str
    role: str # Doctor, Coordinator, Admin
    email: EmailStr
    password: str
    facility_id: int

class StaffUserOut(BaseModel):
    user_id: int
    facility_id: int
    name: str
    role: str
    email: EmailStr
    is_active: bool
    class Config:
        from_attributes = True

# Risk Flag
class RiskFlagCreate(BaseModel):
    flag_type: str # hypertension, hemorrhage_history, anemia, c_section, other

class RiskFlagOut(BaseModel):
    flag_id: int
    plan_id: int
    flag_type: str
    applied_at: datetime
    class Config:
        from_attributes = True

# Postnatal Visit
class PostnatalVisitOut(BaseModel):
    visit_id: int
    plan_id: int
    visit_type: str
    due_date: date
    status: str
    days_overdue: Optional[int] = 0
    completed_date: Optional[date] = None
    note: Optional[str] = None
    class Config:
        from_attributes = True

class VisitCompleteRequest(BaseModel):
    completed_date: date
    note: Optional[str] = None

class VisitMissedRequest(BaseModel):
    reason: str # unreachable, declined, moved

# Patient & Discharge Plan
class PatientCreate(BaseModel):
    name: str
    contact_number: str
    preferred_language: Optional[str] = "English"
    delivery_date: date
    discharge_date: date
    newborn_gender: Optional[str] = None
    newborn_name: Optional[str] = None
    risk_flags: Optional[List[str]] = []

class PatientOut(BaseModel):
    patient_id: int
    facility_id: int
    name: str
    contact_number: str
    preferred_language: str
    delivery_date: date
    discharge_date: date
    created_at: datetime
    class Config:
        from_attributes = True

class DischargePlanOut(BaseModel):
    plan_id: int
    patient_id: int
    created_by: int
    created_at: datetime
    status: str
    risk_flags: List[RiskFlagOut] = []
    visits: List[PostnatalVisitOut] = []
    class Config:
        from_attributes = True

# Family Member & Consent
class FamilyMemberCreate(BaseModel):
    name: str
    relation: str
    contact_number: str
    preferred_language: Optional[str] = "English"
    consent_given: bool = True

class ConsentRecordOut(BaseModel):
    consent_id: int
    family_id: int
    consent_given: bool
    recorded_by: int
    timestamp: datetime
    class Config:
        from_attributes = True

class FamilyMemberOut(BaseModel):
    family_id: int
    patient_id: int
    name: str
    relation: str
    contact_number: str
    preferred_language: str
    latest_consent: Optional[bool] = False
    class Config:
        from_attributes = True

class ConsentUpdateRequest(BaseModel):
    consent_given: bool

# Nudge & Webhooks
class NudgeLogOut(BaseModel):
    nudge_id: int
    visit_id: int
    channel: str
    recipient_type: str
    recipient_contact: str
    sent_at: datetime
    status: str
    message_text: str
    class Config:
        from_attributes = True

class TwilioStatusWebhook(BaseModel):
    MessageSid: Optional[str] = None
    MessageStatus: str # sent, delivered, failed
    To: Optional[str] = None

# Worklist & Detail
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
    risk_flags: List[str] = []

class PatientDetailOut(BaseModel):
    patient: PatientOut
    active_plan: Optional[DischargePlanOut] = None
    family_members: List[FamilyMemberOut] = []
    nudges: List[NudgeLogOut] = []

# Audit Log
class AuditLogOut(BaseModel):
    audit_id: int
    actor_id: Optional[int] = None
    action: str
    entity: str
    entity_id: Optional[int] = None
    timestamp: datetime
    details: Optional[str] = None
    class Config:
        from_attributes = True

# Reports
class VisitTypeOutcome(BaseModel):
    visit_type: str
    total: int
    completed: int
    missed: int
    overdue: int
    completion_rate_pct: float

class OutcomesReportOut(BaseModel):
    start_date: date
    end_date: date
    total_patients: int
    total_visits: int
    completed_visits: int
    missed_visits: int
    overdue_visits: int
    overall_completion_rate_pct: float
    outcomes_by_visit_type: List[VisitTypeOutcome]
