import os
import sys

sys.path.append(os.path.dirname(__file__))

from db import get_process, get_process_steps, get_forms
from retrieval import retrieve_scored
from prompts.templates import build_process_guidance_prompt, build_selection_prompt
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
        "understood": "Closest verified question",
        "related": "Related questions you can ask",
        "language_name": "English",
    },
    "ar": {
        "process": "العملية",
        "steps": "الخطوات",
        "forms": "النماذج المطلوبة",
        "verify": "تحقق مع",
        "not_found": "لم أجد هذا في قاعدة البيانات المؤسسية. يرجى التواصل مع عمادة القبول والتسجيل مباشرة.",
        "understood": "أقرب سؤال موثّق",
        "related": "أسئلة ذات صلة يمكنك طرحها",
        "language_name": "Arabic",
    },
}

# ---------------------------------------------------------------------------
# Confidence gate. Tuned on demo/eval_questions.py DEV only; the HELDOUT set
# is the honest measurement (run: python demo/eval_retrieval.py).
#
# A document may be used as the answer only if:
#   - it shares at least MIN_SHARED distinct terms with the question
#     (or all of them, for one-term questions), and
#   - it covers at least MIN_COVERAGE of the question's distinct terms,
#     where terms found nowhere in the data still count against it.
# Otherwise the agent refuses, logs the question as a gap, and it reaches
# the staff email digest. Raising MIN_COVERAGE -> fewer wrong answers,
# more refusals of questions that did have an answer.
# ---------------------------------------------------------------------------
MIN_SHARED = 2
MIN_COVERAGE = 0.6
LLM_CANDIDATES = 3


def _passes_gate(c, n_terms):
    return (
        c["score"] > 0
        and c["shared"] >= min(MIN_SHARED, n_terms)
        and c["coverage"] >= MIN_COVERAGE
    )


def route_question(question, language=None):
    """Decides WHERE an answer may come from — before anything is written.

    Returns a dict:
      source   "faq:<id>", "process:<id>", or None (refuse)
      faq      the chosen FAQ row or None
      process  the process row to show steps/forms for, or None
      lang     "en" / "ar"
      coverage, score   of the chosen record (0 when refusing)
      reason   short text for logs/debugging
    """
    candidates, lang, terms = retrieve_scored(question, language=language)
    passing = [c for c in candidates if _passes_gate(c, len(terms))]
    faqs = [c for c in passing if c["type"] == "faq"]
    procs = [c for c in passing if c["type"] == "process"]

    chosen = None
    if _llm_configured() and (faqs or procs):
        chosen = _llm_select(question, (faqs + procs)[:LLM_CANDIDATES], lang)
        reason = "llm-selected" if chosen else "llm-rejected all candidates"
    elif faqs:
        chosen, reason = faqs[0], "top faq above gate"
    elif procs:
        chosen, reason = procs[0], "top process above gate (no faq passed)"
    else:
        best = candidates[0] if candidates else None
        reason = ("no candidate passed the gate"
                  + (f" (best coverage {best['coverage']:.2f})" if best else ""))

    if not chosen:
        return {"source": None, "faq": None, "process": None, "lang": lang,
                "coverage": 0.0, "score": 0.0, "reason": reason}

    faq = chosen["record"] if chosen["type"] == "faq" else None
    process = None
    if faq and faq.get("process_id"):
        # the FAQ pins down its process — fetch it by id (see db.get_process)
        process = get_process(faq["process_id"])
    elif chosen["type"] == "process":
        process = chosen["record"]
    return {"source": f"{chosen['type']}:{chosen['id']}", "faq": faq, "process": process,
            "lang": lang, "coverage": chosen["coverage"], "score": chosen["score"],
            "reason": reason}


def _llm_configured():
    return os.environ.get("LLM_PROVIDER") == "anthropic" and bool(os.environ.get("ANTHROPIC_API_KEY"))


def _llm_select(question, candidates, lang):
    """The model only picks a candidate number or NONE. Anything else it
    returns (an explanation, an answer, a number out of range) is treated
    as NONE — a refusal, never a guess."""
    q_k, a_k = ("question_ar", "answer_ar") if lang == "ar" else ("question", "answer")
    name_k, desc_k = ("name_ar", "description_ar") if lang == "ar" else ("name", "description")
    lines = []
    for i, c in enumerate(candidates, 1):
        r = c["record"]
        if c["type"] == "faq":
            lines.append(f"{i}. Q: {strip_prompt_injection(r[q_k])} A: {strip_prompt_injection(r[a_k])}")
        else:
            lines.append(f"{i}. PROCESS: {strip_prompt_injection(r[name_k])} — {strip_prompt_injection(r[desc_k])}")
    reply = _call_llm(build_selection_prompt(question, "\n".join(lines)))
    if reply is None:
        return candidates[0] if candidates else None
    reply = reply.strip().upper()
    if reply.isdigit() and 1 <= int(reply) <= len(candidates):
        return candidates[int(reply) - 1]
    return None


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
    so the agent still runs (offline mode) for demos without API cost.

    Since the "no generated answers" change, this is only ever called with
    the SELECTION prompt: the model returns a candidate number, not prose."""
    provider = os.environ.get("LLM_PROVIDER")
    if provider == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=5,
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
        out.append(f"{L['understood']}: {faqs[0][q_k]}")
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
        if faqs:
            related = [r for r in _faqs_for_process(p["id"], lang) if r["id"] != faqs[0]["id"]]
            if related:
                out.append(f"\n{L['related']}:")
                for r in related:
                    out.append(f"  - {r[q_k]}")
        out.append(f"\n{L['verify']}: {p[office_k]}")
    elif faqs:
        # FAQ with no linked process (e.g. one added via add_faq.py without
        # a process_id) — still owe the user a verify line, sourced from
        # who verified the FAQ rather than a process office.
        out.append(f"\n{L['verify']}: {faqs[0][verified_by_k]}")
    return "\n".join(out)


def _faqs_for_process(process_id, lang):
    from db import get_conn
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM faqs WHERE process_id = ? ORDER BY id", (process_id,))]
    conn.close()
    if lang == "ar":
        rows = [r for r in rows if r.get("question_ar")]
    return rows


def answer_question(question, role="student", language=None):
    """Main entry point. Returns (answer_text, prompt_used, qa_passed).

    Pipeline:
      1. route_question() picks the ONE verified record allowed to answer,
         or refuses if nothing clears the confidence gate.
      2. The answer is rendered from that record verbatim
         (_offline_fallback) — in the question's language, with the
         matched question shown so the student can see what was understood.
      3. QA (grounding + verify line) runs on the result and everything is
         logged; a refusal fails QA and becomes a gap in /admin/unanswered.

    There is no generated free text anywhere in this path, with or without
    an LLM configured: the LLM, when present, only chooses between records
    (see _llm_select)."""
    route = route_question(question, language=language)
    lang = route["lang"]
    faqs = [route["faq"]] if route["faq"] else []
    processes = [route["process"]] if route["process"] else []

    context = _format_context(processes, faqs, lang)
    prompt = build_process_guidance_prompt(question, role, context, LABELS[lang]["language_name"])
    answer = _offline_fallback(processes, faqs, role, lang)

    qa = review_process_guidance(answer, context, lang)
    notes = list(qa.notes) + [f"route: {route['reason']}"]
    log_interaction(
        question=question,
        process_ids=[p["id"] for p in processes],
        faq_ids=[f["id"] for f in faqs],
        qa_passed=qa.passed,
        qa_notes=notes,
        language=lang,
    )
    return answer, prompt, qa.passed
