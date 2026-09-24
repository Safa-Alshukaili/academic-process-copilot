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


def unanswered_questions(limit=50):
    """Groups failed (qa_passed=0) questions by exact text, with how many
    times each was asked and when it was last asked. This is the queue a
    staff member works from: the questions at the top (asked most) are
    the highest-value gaps to close first in data/seed.py or via
    add_faq.py, since closing one fixes it for every student who asks
    that question afterward."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT question, COUNT(*) as times_asked, MAX(timestamp) as last_asked
        FROM audit_log
        WHERE qa_passed = 0
        GROUP BY question
        ORDER BY times_asked DESC, last_asked DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def kpi_summary(last_n=100, top_gaps=5):
    """One aggregated view of system health — the piece that was missing
    even though the underlying signals (failure_rate, unanswered_questions,
    freshness) already existed separately. For an IT Support/Technician
    role specifically, this is the difference between having built a
    system and being able to say how it's doing right now without
    stitching three endpoints together by hand.

    Kept honest: total_questions_logged is a lifetime count (not windowed)
    so it doesn't imply more recent activity than there's been; qa_pass_rate
    is explicitly windowed to the last `last_n` so a single bad day doesn't
    stay baked into the number forever."""
    all_rows = recent(100000)  # audit_log is small at this project's scale
    total_questions = len(all_rows)

    windowed = recent(last_n)
    qa_pass_rate = None
    if windowed:
        passed = sum(1 for r in windowed if r["qa_passed"] == 1)
        qa_pass_rate = round(passed / len(windowed), 3)

    gaps = unanswered_questions(limit=top_gaps)

    from freshness_check import check as freshness_check
    stale_faq_count = len(freshness_check())

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM faqs")
    total_faqs = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM processes")
    total_processes = cur.fetchone()["c"]
    conn.close()

    return {
        "total_questions_logged": total_questions,
        "qa_pass_rate_last_n": qa_pass_rate,
        "qa_pass_rate_window": min(last_n, len(windowed)) if windowed else 0,
        "top_unanswered_gaps": gaps,
        "stale_faq_count": stale_faq_count,
        "total_faqs": total_faqs,
        "total_processes": total_processes,
    }
