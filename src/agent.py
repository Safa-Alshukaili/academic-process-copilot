import os
import sys

sys.path.append(os.path.dirname(__file__))

from db import get_process_steps, get_forms
from retrieval import retrieve
from prompts.templates import build_process_guidance_prompt
from security import strip_prompt_injection
from qa_review import review_process_guidance
from audit_log import log_interaction


def _format_context(processes, faqs):
    """Turns raw DB rows into the CONTEXT block for the prompt.
    Every row is sanitized against prompt injection before being inserted —
    institutional data can come from many contributors, so it is treated
    as untrusted input, not as trusted instructions."""
    lines = []
    for p in processes:
        lines.append(f"PROCESS: {strip_prompt_injection(p['name'])}")
        lines.append(f"  Description: {strip_prompt_injection(p['description'])}")
        lines.append(f"  Responsible office: {p['responsible_office']}")
        steps = get_process_steps(p["id"])
        for s in steps:
            lines.append(
                f"  Step {s['step_number']}: {strip_prompt_injection(s['title'])} — "
                f"{strip_prompt_injection(s['description'])} "
                f"(Docs: {s['required_documents'] or 'none'})"
            )
        for f in get_forms(p["id"]):
            lines.append(f"  Form: {f['form_name']} — {f['form_location']}")
    for fq in faqs:
        lines.append(
            f"FAQ: Q: {strip_prompt_injection(fq['question'])} "
            f"A: {strip_prompt_injection(fq['answer'])} "
            f"(verified {fq['last_verified_date']} by {fq['verified_by']})"
        )
    return "\n".join(lines) if lines else "No matching institutional data found."


def _call_llm(prompt):
    """Pluggable LLM call. Reads a provider from env so the same agent can
    run against Gemini, Claude, or OpenAI without code changes — set
    LLM_PROVIDER and the matching API key. Returns None if no key is set,
    so the agent still runs (offline mode) for demos without API cost."""
    provider = os.environ.get("LLM_PROVIDER")
    if provider == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    # Other providers (Gemini/OpenAI) would be added here the same way.
    return None


def _offline_fallback(processes, faqs, role):
    """Deterministic, template-based answer used when no LLM key is configured.
    This is what keeps the OUTPUT FORMAT contract even without an API call —
    useful both for cost-free demos and as a safe fallback if the LLM is down."""
    if not processes and not faqs:
        return ("I couldn't find this in the institutional database. "
                "Please contact the Registrar directly.")

    out = []
    if faqs:
        out.append(faqs[0]["answer"])
    if processes:
        p = processes[0]
        out.append(f"\nProcess: {p['name']} ({p['description']})")
        steps = get_process_steps(p["id"])
        if steps:
            out.append("Steps:")
            for s in steps:
                out.append(f"  {s['step_number']}. {s['title']} — {s['description']}")
        forms = get_forms(p["id"])
        if forms:
            out.append("Required form(s):")
            for f in forms:
                out.append(f"  - {f['form_name']}: {f['form_location']}")
        out.append(f"\nVerify with: {p['responsible_office']}")
    elif faqs:
        # FAQ with no linked process (e.g. one added via add_faq.py without
        # a process_id) — still owe the user a verify line, sourced from
        # who verified the FAQ rather than a process office.
        out.append(f"\nVerify with: {faqs[0]['verified_by']}")
    return "\n".join(out)


def answer_question(question, role="student", language="English"):
    """Main entry point: retrieve verified context via BM25 (src/retrieval.py),
    build the structured prompt, call the LLM if configured, else fall
    back to a deterministic templated answer. Returns
    (answer_text, prompt_used, qa_passed) so both the prompt and the
    grounding verdict are always inspectable — important for review/audit.

    Only the single top-ranked FAQ is kept for the offline fallback (which
    only ever reads faqs[0]) — returning several ranked-but-unused FAQs
    was pure noise with no effect on the answer."""
    processes, faqs = retrieve(question)
    faqs = faqs[:1]

    # if the FAQ pins down a specific process, prefer that process alone
    # over other loosely-matched ones — the FAQ is the more precise signal
    faq_process_ids = {f["process_id"] for f in faqs if f.get("process_id")}
    if faq_process_ids:
        narrowed = [p for p in processes if p["id"] in faq_process_ids]
        if narrowed:
            processes = narrowed

    context = _format_context(processes, faqs)
    prompt = build_process_guidance_prompt(question, role, context, language)

    llm_answer = _call_llm(prompt)
    answer = llm_answer if llm_answer is not None else _offline_fallback(processes, faqs, role)

    qa = review_process_guidance(answer, context)
    log_interaction(
        question=question,
        process_ids=[p["id"] for p in processes],
        faq_ids=[f["id"] for f in faqs],
        qa_passed=qa.passed,
        qa_notes=qa.notes,
    )
    return answer, prompt, qa.passed
