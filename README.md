# Academic Process Copilot

An AI-assisted institutional process assistant: a student (or advisor) asks
a question about a university procedure, and a structured-prompting agent
answers from a verified database, guides them through the required steps
and forms, and refuses to guess when the data doesn't cover the question.
A second module applies the same structured-prompting + QA pattern to
drafting and reviewing academic materials.

Built specifically to demonstrate every capability an
**AI-Enabled Academic and Administrative Support IT Technician** role
requires — this README maps each requirement to exactly where it's
implemented, so nothing has to be taken on faith.

> Sample data only. The institutional processes, forms and FAQs in
> `data/seed.py` are modeled on typical Omani university procedures for
> demonstration — replace with real institutional data before any real use.

## Quick start

```bash
pip install -r requirements.txt   # optional — stdlib-only for the offline demo
python data/seed.py               # builds data/institutional_processes.db
python demo/demo.py               # runs both flows end to end
python demo/test_qa_review.py     # QA layer tests, including failure cases
```

Runs fully offline by default (no API key needed) using a deterministic
template fallback — set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`
to route through a real model instead; see `src/agent.py::_call_llm`.

## Requirement → implementation map

| Job description requirement | Where it's implemented |
|---|---|
| Develop, organize and maintain structured academic resources in line with curriculum frameworks and quality standards | `src/materials.py`, `src/prompts/templates.py::MATERIAL_REVIEW_TEMPLATE` (curriculum requirements + quality checklist are explicit inputs) |
| Apply AI-assisted tools and structured prompts to develop, refine and review academic materials within agreed guidelines | `src/materials.py::draft_and_review()`, `src/prompts/templates.py` |
| Support academic teams in consistent review, verification and quality assurance processes | `src/qa_review.py`, `docs/QA_PROCESS.md` |
| Build and maintain databases and repositories covering institutional stakeholders and academic operations | `data/seed.py` (schema + seed), `src/db.py` |
| Design AI-assisted workflows and agents that reduce repetitive administrative work and guide users through forms and institutional processes | `src/agent.py::answer_question()`, Demo 1 in `demo/demo.py` |
| Work with academic and administrative staff to identify where AI and digital tools can improve existing processes | `docs/PROCESS_IMPROVEMENT_ANALYSIS.md` |
| Provide technical support for implementing and improving AI-enabled institutional solutions | "Running this yourself" section below + `docs/RESPONSIBLE_AI_AND_SECURITY.md` "what a real deployment would add" |
| Demonstrated use of generative AI tools in a professional/academic setting | Whole project; pluggable LLM call in `src/agent.py::_call_llm` |
| Sound understanding of structured prompting for information processing and workflow support | `src/prompts/templates.py` — fixed role, verified context, explicit output format and guardrails, not a free-form instruction |
| Strong digital literacy across databases, spreadsheets and online platforms | SQLite schema design (`data/seed.py`), CLI tooling |
| Minimum 2 years' experience; **or** strong graduate with demonstrable AI projects | This project is that evidence |
| AI agents, workflow automation, or no-code/low-code platforms | `src/agent.py` (code-based agent); see "No-code equivalent" below for the low-code framing |
| Database design and data management | `data/seed.py` schema (5 normalized tables, foreign keys, seed data) |
| University, educational environment | Domain of the whole project |
| Quality assurance and structured documentation processes | `docs/QA_PROCESS.md`, `src/qa_review.py`, tests in `demo/test_qa_review.py` |
| Data protection, information security and responsible AI use | `docs/RESPONSIBLE_AI_AND_SECURITY.md`, `src/security.py` |

## Architecture

```
data/seed.py        → builds institutional_processes.db (stakeholders,
                       processes, process_steps, forms, faqs)
src/db.py            → read layer, keyword retrieval
src/prompts/         → structured prompt templates (the "how" of the AI use)
src/agent.py          → process-guidance flow: retrieve → build prompt →
                        call LLM (or offline fallback) → return answer + prompt
src/materials.py      → material drafting/refinement flow, same pattern
src/qa_review.py      → automated QA checks (does NOT auto-approve)
src/security.py       → prompt-injection stripping, PII redaction, RBAC stub
demo/demo.py          → runs both flows, prints every stage (nothing hidden)
demo/test_qa_review.py→ QA tests, including cases that should FAIL
docs/                 → QA process, responsible-AI/security policy,
                        process-improvement analysis
```

## No-code equivalent

The same flow (retrieve verified row → structured prompt → guarded output)
maps directly onto a no-code tool like n8n: a Webhook/Chat trigger node →
a Postgres/SQLite node running the same keyword query → a "Set" node that
assembles the CONTEXT block → an AI node with the same structured prompt →
a Function node running the same QA checks before responding. Built here in
code instead of n8n so the structured-prompting logic and QA checks are
fully inspectable and testable (see `demo/test_qa_review.py`), but the
underlying design translates directly to a low-code deployment if that's
the institution's preferred stack.

## Honest limitations

- Retrieval is keyword-based, not semantic (embeddings) — sufficient for a
  small, well-structured process database; would need reworking at scale.
- No admin UI yet — data is seeded via script, not edited through a form.
- Offline fallback mode formats retrieved rows directly rather than
  generating natural free text; that trade-off is intentional (predictable,
  auditable output) but worth knowing about.
