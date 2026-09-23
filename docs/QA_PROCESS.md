# Quality Assurance & Verification Process

This describes the human-in-the-loop workflow around every piece of
AI-assisted output this system produces. The automated checks in
`src/qa_review.py` support this process — they do not replace it.

## 1. Process-guidance answers (the student-facing agent)

1. **Draft**: agent retrieves verified DB rows and generates an answer using
   the structured prompt in `src/prompts/templates.py`.
2. **Automated check**: `qa_review.review_process_guidance()` verifies the
   answer is grounded in retrieved context and ends with a "Verify with:
   <office>" line.
3. **Publication**: because the underlying data (`faqs`, `process_steps`)
   is pre-verified (see `last_verified_date` / `verified_by` columns), a
   passing automated check is sufficient for direct answers to students.
4. **Escalation**: if the automated check fails, or no matching context is
   found, the agent tells the student to contact the responsible office
   directly rather than guessing.
5. **Freshness**: `src/freshness_check.py` (also exposed at `GET
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
