"""
Quality assurance / verification layer.
See docs/QA_PROCESS.md for the human-in-the-loop workflow this supports.

This does NOT approve content. It runs automated checks and produces a
report a human reviewer uses to sign off — the sign-off itself is always
human, per docs/QA_PROCESS.md.
"""
import re
from dataclasses import dataclass, field


@dataclass
class QAReport:
    passed: bool
    checks: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def _extract_numbers(text):
    """Numbers worth checking for grounding — 2+ digit integers, decimals
    (2.00, 3.50), and percentages. Single digits are skipped on purpose:
    they show up constantly as list/step numbering (Step 1, Step 2...) in
    both the answer and the context regardless of topic, so checking them
    produces noise, not signal."""
    return set(re.findall(r"\b\d{2,}(?:\.\d+)?\b|\b\d\.\d+\b|\b\d+%", text))


def _extract_article_refs(text):
    """Article/section citations like 'Article 46' or 'Art. 38.1' — the
    single highest-value thing to verify isn't invented, since a wrong
    article number is exactly the kind of confident-sounding, checkable
    fabrication a real LLM could produce."""
    return set(re.findall(r"(?:Article|Art\.)\s*\d+(?:\.\d+)*", text, flags=re.IGNORECASE))


def check_grounding(answer_text, context_used):
    """Verifies the answer doesn't state a number or article citation that
    isn't actually present in the retrieved context — the concrete,
    testable half of 'generation depends only on the retrieved data'.
    This is what makes the pipeline a real RAG safety check rather than
    just a prompt instruction the model might ignore: it inspects the
    output, it doesn't just ask nicely in the prompt.

    Note what this does and doesn't catch: it catches invented numbers
    and article citations — the highest-stakes, most checkable class of
    hallucination for a regulation-answering agent. It does not catch
    fabricated prose that introduces no numbers/citations (e.g. an
    invented *reason* stated in fluent, number-free language) — that
    would need an entailment check or a second LLM pass, out of scope
    here. Documented as a known limit, not hidden."""
    answer_numbers = _extract_numbers(answer_text)
    context_numbers = _extract_numbers(context_used)
    unsupported_numbers = answer_numbers - context_numbers

    answer_articles = _extract_article_refs(answer_text)
    context_articles = _extract_article_refs(context_used)
    unsupported_articles = {
        a for a in answer_articles
        if not any(a.lower().replace("art.", "article") in c.lower().replace("art.", "article")
                   or c.lower().replace("art.", "article") in a.lower().replace("art.", "article")
                   for c in context_articles)
    }

    notes = []
    if unsupported_numbers:
        notes.append(f"Number(s) in the answer not found in retrieved context: {sorted(unsupported_numbers)}")
    if unsupported_articles:
        notes.append(f"Article citation(s) in the answer not found in retrieved context: {sorted(unsupported_articles)}")

    passed = not unsupported_numbers and not unsupported_articles
    return passed, notes


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

    grounded, grounding_notes = check_grounding(answer_text, context_used)
    checks["grounded_in_context"] = grounded
    notes.extend(grounding_notes)

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
