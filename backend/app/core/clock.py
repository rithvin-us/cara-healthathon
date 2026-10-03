"""Time helpers.

Visit due dates are calendar dates at the facility, so "today" must be the
facility's local date (IST by default), not the server's UTC date. Timestamps
are stored as naive UTC for portability across SQLite and Postgres.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

_facility_tz = ZoneInfo(settings.TIMEZONE)


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def facility_today() -> date:
    return datetime.now(_facility_tz).date()
