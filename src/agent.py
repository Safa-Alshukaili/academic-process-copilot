import os
import sys

sys.path.append(os.path.dirname(__file__))

from db import get_process, get_process_steps, get_forms
from retrieval import retrieve
from prompts.templates import build_process_guidance_prompt
from security import strip_prompt_injection
from qa_review import review_process_guidance
from audit_log import log_interaction

LABELS = {
    "en": {
        "process": "Process",
        "steps": "Steps",
        "forms": "Required form(s)",
        "verify": "Verify with",
        "not_found": "I couldn't find this in the institutional database. Please contact the Registrar directly.",
        "language_name": "English",
    },
    "ar": {
        "process": "العملية",
        "steps": "الخطوات",
        "forms": "النماذج المطلوبة",
        "verify": "تحقق مع",
        "not_found": "لم أجد هذا في قاعدة البيانات المؤسسية. يرجى التواصل مع عمادة القبول والتسجيل مباشرة.",
        "language_name": "Arabic",
    },
}


def _format_context(processes, faqs, lang):
    """Turns raw DB rows into the CONTEXT block for the prompt, in the
    query's own language. Every row is sanitized against prompt
    injection before being inserted — institutional data can come from
    many contributors, so it is treated as untrusted input, not as
    trusted instructions."""
    name_k, desc_k = ("name_ar", "description_ar") if lang == "ar" else ("name", "description")
    office_k = "responsible_office_ar" if lang == "ar" else "responsible_office"
    title_k, step_desc_k = ("title_ar", "description_ar") if lang == "ar" else ("title", "description")
    q_k, a_k = ("question_ar", "answer_ar") if lang == "ar" else ("question", "answer")
    verified_by_k = "verified_by_ar" if lang == "ar" else "verified_by"

    lines = []
    for p in processes:
        lines.append(f"PROCESS: {strip_prompt_injection(p[name_k])}")
        lines.append(f"  Description: {strip_prompt_injection(p[desc_k])}")
        lines.append(f"  Responsible office: {p[office_k]}")
        steps = get_process_steps(p["id"])
        for s in steps:
            lines.append(
                f"  Step {s['step_number']}: {strip_prompt_injection(s[title_k])} — "
                f"{strip_prompt_injection(s[step_desc_k])} "
                f"(Docs: {s['required_documents'] or 'none'})"
            )
        for f in get_forms(p["id"]):
            lines.append(f"  Form: {f['form_name']} — {f['form_location']}")
    for fq in faqs:
        lines.append(
            f"FAQ: Q: {strip_prompt_injection(fq[q_k])} "
            f"A: {strip_prompt_injection(fq[a_k])} "
            f"(verified {fq['last_verified_date']} by {fq[verified_by_k]})"
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


def _offline_fallback(processes, faqs, role, lang):
    """Deterministic, template-based answer used when no LLM key is
    configured — rendered entirely in the query's own language, labels
    included, not just the underlying facts."""
    L = LABELS[lang]
    name_k, desc_k = ("name_ar", "description_ar") if lang == "ar" else ("name", "description")
    office_k = "responsible_office_ar" if lang == "ar" else "responsible_office"
    title_k, step_desc_k = ("title_ar", "description_ar") if lang == "ar" else ("title", "description")
    q_k, a_k = ("question_ar", "answer_ar") if lang == "ar" else ("question", "answer")
    verified_by_k = "verified_by_ar" if lang == "ar" else "verified_by"

    if not processes and not faqs:
        return L["not_found"]

    out = []
    if faqs:
        out.append(faqs[0][a_k])
    if processes:
        p = processes[0]
        out.append(f"\n{L['process']}: {p[name_k]} ({p[desc_k]})")
        steps = get_process_steps(p["id"])
        if steps:
            out.append(f"{L['steps']}:")
            for s in steps:
                out.append(f"  {s['step_number']}. {s[title_k]} — {s[step_desc_k]}")
        forms = get_forms(p["id"])
        if forms:
            out.append(f"{L['forms']}:")
            for f in forms:
                out.append(f"  - {f['form_name']}: {f['form_location']}")
        out.append(f"\n{L['verify']}: {p[office_k]}")
    elif faqs:
        # FAQ with no linked process (e.g. one added via add_faq.py without
        # a process_id) — still owe the user a verify line, sourced from
        # who verified the FAQ rather than a process office.
        out.append(f"\n{L['verify']}: {faqs[0][verified_by_k]}")
    return "\n".join(out)


def answer_question(question, role="student", language=None):
    """Main entry point: detects the question's language, retrieves
    verified context via BM25 in that language (src/retrieval.py), builds
    the structured prompt, calls the LLM if configured, else falls back
    to a deterministic templated answer — also in that language. Returns
    (answer_text, prompt_used, qa_passed).

    `language` can be forced to "en"/"ar" (mainly for tests); left as
    None, it's auto-detected from the question itself.

    Only the single top-ranked FAQ is kept for the offline fallback (which
    only ever reads faqs[0]) — returning several ranked-but-unused FAQs
    was pure noise with no effect on the answer."""
    processes, faqs, lang = retrieve(question, language=language)
    faqs = faqs[:1]

    # if the FAQ pins down a specific process, prefer that process alone
    # over other loosely-matched ones — the FAQ is the more precise signal.
    # Fetch it directly by id rather than only filtering the already-
    # retrieved candidates: a real bug, found during bilingual testing,
    # was that the correct process could be identified via the FAQ but
    # not itself appear in the BM25 top-k, silently leaving a wrong,
    # loosely-matched process in place instead.
    faq_process_ids = {f["process_id"] for f in faqs if f.get("process_id")}
    if faq_process_ids:
        narrowed = [p for p in processes if p["id"] in faq_process_ids]
        if not narrowed:
            narrowed = [p for pid in faq_process_ids if (p := get_process(pid))]
        if narrowed:
            processes = narrowed

    context = _format_context(processes, faqs, lang)
    prompt = build_process_guidance_prompt(question, role, context, LABELS[lang]["language_name"])

    llm_answer = _call_llm(prompt)
    answer = llm_answer if llm_answer is not None else _offline_fallback(processes, faqs, role, lang)

    qa = review_process_guidance(answer, context, lang)
    log_interaction(
        question=question,
        process_ids=[p["id"] for p in processes],
        faq_ids=[f["id"] for f in faqs],
        qa_passed=qa.passed,
        qa_notes=qa.notes,
        language=lang,
    )
    return answer, prompt, qa.passed
