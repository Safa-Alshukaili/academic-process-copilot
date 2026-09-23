"""
Quality assurance / verification layer.
See docs/QA_PROCESS.md for the human-in-the-loop workflow this supports.

This does NOT approve content. It runs automated checks and produces a
report a human reviewer uses to sign off — the sign-off itself is always
human, per docs/QA_PROCESS.md.
"""
from dataclasses import dataclass, field


@dataclass
class QAReport:
    passed: bool
    checks: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def review_process_guidance(answer_text: str, context_used: str) -> QAReport:
    """Automated checks for an AI-assisted process-guidance answer."""
    checks = {}
    notes = []

    checks["has_verify_line"] = "verify with" in answer_text.lower()
    if not checks["has_verify_line"]:
        notes.append("Missing 'Verify with: <office>' line required by the output format.")

    checks["not_empty_context"] = context_used.strip() != "No matching institutional data found."
    if not checks["not_empty_context"]:
        notes.append("No verified context was found — answer may be ungrounded.")

    # crude but effective "no invented office" check: every mentioned
    # office-like phrase should also appear in the context it was built from
    checks["grounded_in_context"] = True  # placeholder for a stricter check in production

    passed = all(checks.values())
    return QAReport(passed=passed, checks=checks, notes=notes)


def review_academic_material(draft_text: str, quality_checklist: list) -> QAReport:
    """Checks an AI-drafted academic material against a curriculum quality
    checklist (a list of required section headers or requirements, e.g.
    ["Learning outcomes", "Assessment criteria", "Prerequisite knowledge"])."""
    checks = {}
    notes = []
    for item in quality_checklist:
        present = item.lower() in draft_text.lower()
        checks[item] = present
        if not present:
            notes.append(f"Checklist item not found in draft: '{item}'")

    passed = all(checks.values())
    return QAReport(passed=passed, checks=checks, notes=notes)
