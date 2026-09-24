import re
from typing import Tuple

# Disallowed clinical terms per SRS (AI-006 & Section 11)
DISALLOWED_CLINICAL_KEYWORDS = [
    r"\bdiagnosis\b", r"\bdiagnose\b", r"\btreatment\b", r"\bdosage\b", r"\bmg\b", r"\bml\b",
    r"\bprescription\b", r"\bprescribe\b", r"\bmedicine\b", r"\bmedication\b", r"\bpill\b",
    r"\btablet\b", r"\binjection\b", r"\btherapy\b", r"\bpathology\b", r"\bcomplication\b",
    r"\binfection\b", r"\bhemorrhage\b", r"\bsymptom\b", r"\btriage\b", r"\bcure\b"
]

SAFE_TEMPLATE_NUDGE = "Hello {mother_name}, this is a reminder for your upcoming postnatal checkup ({visit_type}) scheduled on {due_date} at {facility_name}. Please visit the clinic or contact us to confirm your appointment."

SAFE_TEMPLATE_DIGEST = "Weekly Digest for {facility_name}: {total_overdue} visits are currently overdue across your patient panel. Please review your worklist to complete follow-ups."

class ContentFilter:
    @staticmethod
    def inspect_text(text: str) -> Tuple[bool, str]:
        """
        Scans text for clinical terminology.
        Returns (is_valid: bool, reason: str)
        """
        if not text or not text.strip():
            return False, "Empty text"
            
        lowered = text.lower()
        for pattern in DISALLOWED_CLINICAL_KEYWORDS:
            if re.search(pattern, lowered):
                return False, f"Disallowed clinical term detected: pattern '{pattern}'"
                
        return True, "Passed non-clinical inspection"

    @staticmethod
    def filter_and_fallback_nudge(generated_text: str, mother_name: str, visit_type: str, due_date: str, facility_name: str = "Cara Health Clinic") -> Tuple[str, bool]:
        """
        Returns (final_text, is_fallback_used)
        """
        is_valid, reason = ContentFilter.inspect_text(generated_text)
        if is_valid:
            return generated_text, False
        else:
            fallback = SAFE_TEMPLATE_NUDGE.format(
                mother_name=mother_name,
                visit_type=visit_type,
                due_date=due_date,
                facility_name=facility_name
            )
            return fallback, True

    @staticmethod
    def filter_and_fallback_digest(generated_text: str, facility_name: str, total_overdue: int) -> Tuple[str, bool]:
        is_valid, reason = ContentFilter.inspect_text(generated_text)
        if is_valid:
            return generated_text, False
        else:
            fallback = SAFE_TEMPLATE_DIGEST.format(
                facility_name=facility_name,
                total_overdue=total_overdue
            )
            return fallback, True
