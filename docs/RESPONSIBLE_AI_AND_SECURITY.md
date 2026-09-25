# Data Protection, Information Security & Responsible AI Use

## Data protection

- The `stakeholders` table intentionally stores only **role, department,
  program** — no names, IDs, or contact details. Institutional data about
  people is minimized by design, not redacted after the fact.
- `src/security.py::redact_pii()` masks any PII fields if the schema is
  ever extended to include them (e.g. for a real advisor lookup feature),
  so logs and exports never contain raw PII.
- `src/security.py::check_access()` is a minimal role-based access stub;
  a real deployment would back it with the institution's identity provider
  (e.g. university SSO), not a plain role string.

## Prompt injection / data integrity

- Institutional content (process descriptions, FAQ answers) is edited by
  multiple staff over time and is treated as **untrusted input**, not as
  trusted instructions, before being inserted into a prompt.
- `src/security.py::strip_prompt_injection()` strips common override
  patterns (e.g. "ignore previous instructions") from any DB text before
  it reaches the model. This is a first line of defense — a production
  system would pair it with prompt-level system/user role separation and
  periodic review of stored content, not rely on regex alone.

## Responsible AI use

- The agent never invents institutional facts: the structured prompt in
  `src/prompts/templates.py` explicitly instructs the model to use only
  the retrieved CONTEXT and to say so if the context is insufficient,
  rather than guess — and this is checked, not just requested.
  `src/qa_review.py::check_grounding()` inspects every generated answer
  for numbers and article citations that don't actually appear in the
  retrieved context, so an instruction the model ignores still gets
  caught rather than silently published. See "RAG design" in the main
  README for what this does and doesn't cover.
- The agent never asks the user for personal identifying information.
- No AI-assisted output is published without a human review step — see
  `docs/QA_PROCESS.md`. The AI drafts; a named person approves.
- The offline fallback mode (no LLM key configured) still enforces the
  same output contract, so the system fails safely rather than silently
  degrading to free-form generation.

## Audit logging

`src/audit_log.py` logs every question the agent answers — the question
text, which processes/FAQs matched, and whether the answer passed QA. It
never stores the generated answer text or any user-identifying
information, so the log itself needs no separate protection. `GET /health`
surfaces a rolling QA failure rate from this log as an early-warning
signal for missing data coverage.

## What a real institutional deployment would add

This is a portfolio-scale project. A production version would add:
integration with the institution's SSO for access control, a formal data
protection impact assessment before storing any personal data, and
retention/deletion policies for the audit log itself.
