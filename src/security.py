"""
Data protection and responsible-AI utilities.
See docs/RESPONSIBLE_AI_AND_SECURITY.md for the policy these implement.
"""
import re

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"disregard (the )?(above|system) prompt",
    r"you are now",
    r"act as",
    r"</?(system|instruction)s?>",
]


def strip_prompt_injection(text):
    """Institutional data (process descriptions, FAQ answers) may be edited
    by many staff over time. Before that text is inserted into a prompt as
    CONTEXT, strip anything that looks like an attempt to override the
    agent's instructions. This is a first line of defense, not a complete
    solution — see docs/RESPONSIBLE_AI_AND_SECURITY.md for the full policy."""
    if not text:
        return text
    cleaned = text
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[removed]", cleaned, flags=re.IGNORECASE)
    return cleaned


PII_FIELDS = {"name", "email", "phone", "student_id"}


def redact_pii(record: dict) -> dict:
    """Masks PII fields before a record is logged or exported. The
    stakeholders table intentionally stores role/department/program only —
    no names or contact details — but this exists as a guard for any table
    that is extended to include PII later."""
    redacted = dict(record)
    for field in PII_FIELDS:
        if field in redacted and redacted[field]:
            redacted[field] = "[REDACTED]"
    return redacted


ROLE_PERMISSIONS = {
    "student": {"read_faqs", "read_processes", "read_forms"},
    "advisor": {"read_faqs", "read_processes", "read_forms", "read_stakeholders"},
    "staff": {"read_faqs", "read_processes", "read_forms", "read_stakeholders", "edit_processes"},
}


def check_access(role: str, action: str) -> bool:
    """Minimal RBAC stub — a real deployment would back this with the
    institution's identity provider, not a role string."""
    return action in ROLE_PERMISSIONS.get(role, set())
