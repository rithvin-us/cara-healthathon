"""Append-only audit trail (FR-021).

Entries are added to the caller's session and committed with the change they
describe, so a mutation and its audit record succeed or fail together.
"""

from sqlalchemy.orm import Session

from app.models.models import AuditLog, StaffUser

SYSTEM_ACTOR_ID = 0


def record(
    db: Session,
    *,
    action: str,
    entity: str,
    entity_id: int | None = None,
    details: str | None = None,
    actor: StaffUser | None = None,
    facility_id: int | None = None,
    patient_id: int | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor.user_id if actor else SYSTEM_ACTOR_ID,
        facility_id=facility_id if facility_id is not None else (actor.facility_id if actor else None),
        patient_id=patient_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
    db.flush()
    return entry
