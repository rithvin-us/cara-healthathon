"""Reminder text in the recipient's language.

Templates are logistics only (when and where to come) and never mention
symptoms, diagnoses or treatment. Languages without a reviewed template fall
back to English rather than to machine translation.
"""

from datetime import date

VISIT_LABELS = {
    "English": {
        "24h Checkup": "24-hour checkup",
        "48-72h Checkup": "3-day checkup",
        "7-14d Checkup": "10-day checkup",
        "6wk Checkup": "6-week checkup",
        "Weekly Risk Checkup (Week 1)": "week 1 extra checkup",
        "Weekly Risk Checkup (Week 2)": "week 2 extra checkup",
        "Weekly Risk Checkup (Week 3)": "week 3 extra checkup",
        "Weekly Risk Checkup (Week 4)": "week 4 extra checkup",
        "Post-op/Anemia Checkup (Week 2)": "week 2 extra checkup",
        "Post-op/Anemia Checkup (Week 4)": "week 4 extra checkup",
        "Specialist Follow-Up": "specialist appointment",
    },
    "Hindi": {
        "24h Checkup": "24 घंटे की जाँच",
        "48-72h Checkup": "3 दिन की जाँच",
        "7-14d Checkup": "10 दिन की जाँच",
        "6wk Checkup": "6 हफ़्ते की जाँच",
        "Weekly Risk Checkup (Week 1)": "पहले हफ़्ते की अतिरिक्त जाँच",
        "Weekly Risk Checkup (Week 2)": "दूसरे हफ़्ते की अतिरिक्त जाँच",
        "Weekly Risk Checkup (Week 3)": "तीसरे हफ़्ते की अतिरिक्त जाँच",
        "Weekly Risk Checkup (Week 4)": "चौथे हफ़्ते की अतिरिक्त जाँच",
        "Post-op/Anemia Checkup (Week 2)": "दूसरे हफ़्ते की अतिरिक्त जाँच",
        "Post-op/Anemia Checkup (Week 4)": "चौथे हफ़्ते की अतिरिक्त जाँच",
        "Specialist Follow-Up": "विशेषज्ञ से मुलाक़ात",
    },
    "Tamil": {
        "24h Checkup": "24 மணி நேர பரிசோதனை",
        "48-72h Checkup": "3 ஆம் நாள் பரிசோதனை",
        "7-14d Checkup": "10 ஆம் நாள் பரிசோதனை",
        "6wk Checkup": "6 ஆம் வார பரிசோதனை",
        "Weekly Risk Checkup (Week 1)": "1 ஆம் வார கூடுதல் பரிசோதனை",
        "Weekly Risk Checkup (Week 2)": "2 ஆம் வார கூடுதல் பரிசோதனை",
        "Weekly Risk Checkup (Week 3)": "3 ஆம் வார கூடுதல் பரிசோதனை",
        "Weekly Risk Checkup (Week 4)": "4 ஆம் வார கூடுதல் பரிசோதனை",
        "Post-op/Anemia Checkup (Week 2)": "2 ஆம் வார கூடுதல் பரிசோதனை",
        "Post-op/Anemia Checkup (Week 4)": "4 ஆம் வார கூடுதல் பரிசோதனை",
        "Specialist Follow-Up": "நிபுணர் சந்திப்பு",
    },
}

TEMPLATES = {
    "English": {
        "mother_due": (
            "Hello {name}, this is {facility}. Your {visit} is due on {date}. "
            "Please visit the hospital or call us to confirm a time."
        ),
        "mother_overdue": (
            "Hello {name}, this is {facility}. Your {visit} was due on {date}. "
            "Please visit the hospital or call us so we can see you and your baby soon."
        ),
        "family": (
            "Hello {name}, this is {facility}. {mother}'s {visit} is due on {date}. "
            "Please help her visit the hospital, or call us if she needs another time."
        ),
        "family_overdue": (
            "Hello {name}, this is {facility}. {mother}'s {visit} was due on {date}. "
            "Please help her visit the hospital soon, or call us."
        ),
    },
    "Hindi": {
        "mother_due": (
            "नमस्ते {name}, यह {facility} से संदेश है। आपकी {visit} {date} को है। "
            "कृपया अस्पताल आएँ या समय तय करने के लिए हमें कॉल करें।"
        ),
        "mother_overdue": (
            "नमस्ते {name}, यह {facility} से संदेश है। आपकी {visit} {date} को होनी थी। "
            "कृपया जल्द अस्पताल आएँ या हमें कॉल करें, ताकि हम आपसे और आपके शिशु से मिल सकें।"
        ),
        "family": (
            "नमस्ते {name}, यह {facility} से संदेश है। {mother} की {visit} {date} को है। "
            "कृपया उन्हें अस्पताल आने में मदद करें, या दूसरा समय चाहिए तो हमें कॉल करें।"
        ),
        "family_overdue": (
            "नमस्ते {name}, यह {facility} से संदेश है। {mother} की {visit} {date} को होनी थी। "
            "कृपया उन्हें जल्द अस्पताल आने में मदद करें, या हमें कॉल करें।"
        ),
    },
    "Tamil": {
        "mother_due": (
            "வணக்கம் {name}, இது {facility} இலிருந்து வரும் செய்தி. உங்கள் {visit} {date} அன்று உள்ளது. "
            "தயவுசெய்து மருத்துவமனைக்கு வாருங்கள் அல்லது நேரத்தை உறுதிசெய்ய எங்களை அழையுங்கள்."
        ),
        "mother_overdue": (
            "வணக்கம் {name}, இது {facility} இலிருந்து வரும் செய்தி. உங்கள் {visit} {date} அன்று இருந்தது. "
            "உங்களையும் உங்கள் குழந்தையையும் விரைவில் சந்திக்க, தயவுசெய்து மருத்துவமனைக்கு வாருங்கள் அல்லது எங்களை அழையுங்கள்."
        ),
        "family": (
            "வணக்கம் {name}, இது {facility} இலிருந்து வரும் செய்தி. {mother} அவர்களின் {visit} {date} அன்று உள்ளது. "
            "அவர் மருத்துவமனைக்கு வர உதவுங்கள், அல்லது வேறு நேரம் தேவைப்பட்டால் எங்களை அழையுங்கள்."
        ),
        "family_overdue": (
            "வணக்கம் {name}, இது {facility} இலிருந்து வரும் செய்தி. {mother} அவர்களின் {visit} {date} அன்று இருந்தது. "
            "அவர் விரைவில் மருத்துவமனைக்கு வர உதவுங்கள், அல்லது எங்களை அழையுங்கள்."
        ),
    },
}


def resolve_language(language: str | None) -> str:
    return language if language in TEMPLATES else "English"


def visit_label(visit_type: str, language: str) -> str:
    return VISIT_LABELS[resolve_language(language)].get(visit_type, VISIT_LABELS["English"].get(visit_type, visit_type))


RISK_LABELS = {
    "hypertension": "high blood pressure",
    "hemorrhage_history": "PPH history",
    "anemia": "severe anaemia",
    "c_section": "C-section",
    "other": "other risk",
}


def describe_risks(flags) -> str:
    return ", ".join(RISK_LABELS.get(f, f) for f in flags)


_STAFF_LABELS = {
    **{f"Weekly Risk Checkup (Week {n})": f"Week {n} high-risk check" for n in (1, 2, 3, 4)},
    **{f"Post-op/Anemia Checkup (Week {n})": f"Week {n} recovery check" for n in (2, 4)},
}


def describe_visit(visit_type: str) -> str:
    """Staff-facing English label (audit log), matching the dashboard's wording."""
    label = _STAFF_LABELS.get(visit_type) or visit_label(visit_type, "English")
    return label[:1].upper() + label[1:]


def format_date(value: date, language: str) -> str:
    if resolve_language(language) == "English":
        return f"{value.day} {value.strftime('%b %Y')}"
    return value.strftime("%d/%m/%Y")


def render(
    kind: str, language: str, *, name: str, facility: str, visit_type: str, due_date: date, mother: str = ""
) -> str:
    lang = resolve_language(language)
    return TEMPLATES[lang][kind].format(
        name=name,
        facility=facility,
        visit=visit_label(visit_type, lang),
        date=format_date(due_date, lang),
        mother=mother,
    )
