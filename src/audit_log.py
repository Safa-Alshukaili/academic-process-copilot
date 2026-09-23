"""
Audit logging. Every question the agent answers is logged with what
matched and whether it passed QA — this is what "responsible AI use" and
"quality assurance ... processes" mean in an operational sense, not just
on paper. See docs/RESPONSIBLE_AI_AND_SECURITY.md.

Only the question, matched IDs, and QA result are stored — never the
generated answer text or any user-identifying information, so the log
itself carries no PII to protect.
"""
import sys
import os
import sqlite3
import datetime

sys.path.append(os.path.dirname(__file__))
from db import get_conn


def log_interaction(question, process_ids, faq_ids, qa_passed, qa_notes):
    conn = get_conn()
    conn.execute(
        "INSERT INTO audit_log (timestamp, question, matched_process_ids, "
        "matched_faq_ids, qa_passed, qa_notes) VALUES (?, ?, ?, ?, ?, ?)",
        (
            datetime.datetime.utcnow().isoformat(),
            question,
            ",".join(str(i) for i in process_ids),
            ",".join(str(i) for i in faq_ids),
            1 if qa_passed else 0,
            "; ".join(qa_notes),
        ),
    )
    conn.commit()
    conn.close()


def recent(limit=20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def failure_rate(last_n=100):
    """Quick health signal: what fraction of recent answers failed QA.
    A rising failure rate usually means the database is missing coverage
    for questions students are actually asking — a real early-warning
    signal, not just a vanity metric."""
    rows = recent(last_n)
    if not rows:
        return 0.0
    failed = sum(1 for r in rows if r["qa_passed"] == 0)
    return round(failed / len(rows), 3)
