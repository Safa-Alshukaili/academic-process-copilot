# Quality Assurance & Verification Process

This describes the human-in-the-loop workflow around every piece of
AI-assisted output this system produces. The automated checks in
`src/qa_review.py` support this process — they do not replace it.

## 1. Process-guidance answers (the student-facing agent)

1. **Draft**: the agent selects one verified DB record through the
   confidence gate in `src/agent.py::route_question` (optionally confirmed
   by an LLM that may only pick a record number or NONE) and shows it
   verbatim, with the matched question. No answer text is generated.
2. **Automated check**: `qa_review.review_process_guidance()` verifies the
   answer is grounded in retrieved context and ends with a "Verify with:
   <office>" line.
3. **Publication**: because the underlying data (`faqs`, `process_steps`)
   is pre-verified (see `last_verified_date` / `verified_by` columns), a
   passing automated check is sufficient for direct answers to students.
4. **Escalation**: if the automated check fails, or no matching context is
   found, or the confidence gate refuses, the agent tells the student to contact the responsible office
   directly rather than guessing. Every escalation is logged (`src/audit_log.py`)
   with the exact question text.
5. **Closing the loop**: `GET /admin/unanswered` groups logged failures by
   question, most-asked first — this is the staff work queue, not a log
   dump. A staff member reviews the top of that queue, confirms the correct
   answer against the real source, and runs `src/add_faq.py` to publish it
   as a new verified FAQ. This does **not** re-run `data/seed.py` — seeding
   wipes and rebuilds the whole database, including audit history, so it's
   for initial setup only, never for adding one answer. The next student
   who asks the same (or similarly worded) question gets it automatically;
   the old failed attempts stay in the audit log as a record that the gap
   existed and was closed, not because the questions need re-answering.
   In the `automation/` n8n workflow, the "Notify Staff" node is where a
   real deployment would push this alert immediately (e.g. an email per
   escalation) instead of relying on staff to poll `/admin/unanswered`.
6. **Freshness**: `src/freshness_check.py` (also exposed at `GET
   /admin/freshness`) flags any FAQ/process row not re-verified within 180
   days. Re-verifying the flagged content is still a manual step for a
   named staff member — the check only surfaces what needs attention.

## 2. Academic material drafting/refinement

1. **Draft**: `materials.draft_and_review()` generates a draft against a
   named curriculum-requirements string and a quality checklist.
2. **Automated check**: `qa_review.review_academic_material()` verifies
   every checklist item is present in the draft.
3. **Human sign-off (required, not optional)**: an academic staff member
   reviews the draft against the curriculum framework and either approves,
   edits, or rejects it. The AI output is never published without this
   step — the checklist only tells the reviewer what to look for, it does
   not certify accuracy or curriculum fit.
4. **Sign-off log**: each approval should record reviewer name, date, and
   version reviewed (a `material_reviews` table would hold this in a full
   deployment — see README "Next steps").

## 3. Versioning

Every AI-assisted draft is timestamped and kept alongside its QA report and
the exact prompt used to generate it, so a reviewer (or an auditor) can
trace any published content back to the data and prompt that produced it.
