"""
Academic material development/refinement — covers "apply AI-assisted tools
and structured prompts to develop, refine and review academic materials
within agreed guidelines" as a distinct flow from process guidance.
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

from prompts.templates import build_material_review_prompt
from qa_review import review_academic_material
from agent import _call_llm  # reuse the same pluggable LLM call


DEFAULT_CHECKLIST = ["Learning outcomes", "Assessment criteria", "Prerequisite knowledge"]


def _offline_fallback_material(topic, checklist):
    """Deterministic draft used when no LLM key is configured, so the
    checklist/QA loop is demonstrable without an API call."""
    sections = "\n".join(f"## {item}\n[to be completed by reviewer]\n" for item in checklist)
    return f"# Study Guide: {topic}\n\n{sections}"


def draft_and_review(topic, curriculum_requirements, checklist=None):
    """Drafts a study guide via structured prompting, then runs it through
    the QA checklist. Returns (draft, qa_report, prompt_used) — nothing here
    is auto-published; see docs/QA_PROCESS.md for the human sign-off step."""
    checklist = checklist or DEFAULT_CHECKLIST
    checklist_text = "\n".join(f"- {c}" for c in checklist)

    prompt = build_material_review_prompt(
        task="Draft a concise study guide section for academic staff to review.",
        topic=topic,
        curriculum_requirements=curriculum_requirements,
        quality_checklist=checklist_text,
    )

    draft = _call_llm(prompt)
    if draft is None:
        draft = _offline_fallback_material(topic, checklist)

    qa_report = review_academic_material(draft, checklist)
    return draft, qa_report, prompt
