"""Non-clinical content safety filter (AI-006).

Every outbound message and every free-text visit note passes through here.
Anything that looks like clinical advice is rejected and outbound messages
fall back to a pre-approved template.
"""

import re

DISALLOWED_CLINICAL_KEYWORDS = [
    r"\bdiagnos(is|e|ed)\b",
    r"\btreatment\b",
    r"\bdosage\b",
    r"\bdose\b",
    r"\d+\s?mg\b",
    r"\bmg\b",
    r"\bml\b",
    r"\bprescription\b",
    r"\bprescribe(d)?\b",
    r"\bmedicine\b",
    r"\bmedication\b",
    r"\bpills?\b",
    r"\btablets?\b",
    r"\binjection\b",
    r"\btherapy\b",
    r"\bpathology\b",
    r"\bcomplications?\b",
    r"\binfection\b",
    r"\bhemorrhage\b",
    r"\bhaemorrhage\b",
    r"\bsymptoms?\b",
    r"\btriage\b",
    r"\bcure\b",
    r"\bantibiotics?\b",
    r"\bbp\s?\d",
    r"\bhb\s?\d",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in DISALLOWED_CLINICAL_KEYWORDS]

SAFE_TEMPLATE_NUDGE = (
    "Hello {mother_name}, this is a reminder for your postnatal checkup ({visit_type}) on {due_date} "
    "at {facility_name}. Please visit the hospital or call us to confirm your appointment."
)

SAFE_TEMPLATE_DIGEST = (
    "Weekly summary for {facility_name}: {total_overdue} visits are overdue. Please review the follow-up list."
)


class ContentFilter:
    @staticmethod
    def inspect_text(text: str) -> tuple[bool, str]:
        """Returns (is_valid, reason)."""
        if not text or not text.strip():
            return False, "Empty text"
        for pattern in _COMPILED:
            match = pattern.search(text)
            if match:
                return False, f"Disallowed clinical term detected: '{match.group(0)}'"
        return True, "Passed non-clinical inspection"

    @staticmethod
    def filter_and_fallback_nudge(
        generated_text: str, mother_name: str, visit_type: str, due_date: str, facility_name: str = "the hospital"
    ) -> tuple[str, bool]:
        """Returns (final_text, is_fallback_used)."""
        is_valid, _ = ContentFilter.inspect_text(generated_text)
        if is_valid:
            return generated_text, False
        return (
            SAFE_TEMPLATE_NUDGE.format(
                mother_name=mother_name, visit_type=visit_type, due_date=due_date, facility_name=facility_name
            ),
            True,
        )

    @staticmethod
    def filter_and_fallback_digest(generated_text: str, facility_name: str, total_overdue: int) -> tuple[str, bool]:
        is_valid, _ = ContentFilter.inspect_text(generated_text)
        if is_valid:
            return generated_text, False
        return SAFE_TEMPLATE_DIGEST.format(facility_name=facility_name, total_overdue=total_overdue), True
