"""
Tests for the audit log and freshness check — run with:
python demo/test_audit_and_freshness.py

Uses a temporary copy of the database so it never pollutes the real
demo data or the committed institutional_processes.db.
"""
import os
import sys
import shutil
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


def setup_temp_db():
    real_db = os.path.join(os.path.dirname(__file__), "..", "data", "institutional_processes.db")
    tmp_dir = tempfile.mkdtemp()
    tmp_db = os.path.join(tmp_dir, "institutional_processes.db")
    shutil.copy(real_db, tmp_db)
    import db
    db.DB_PATH = tmp_db
    return tmp_dir


def test_audit_log_records_interaction():
    from agent import answer_question
    from audit_log import recent

    before = len(recent(limit=1000))
    answer_question("How many credit hours do I need for OJT?")
    after = recent(limit=1000)
    assert len(after) == before + 1
    assert after[0]["question"] == "How many credit hours do I need for OJT?"
    assert after[0]["qa_passed"] == 1
    print("PASS: audit log records a new interaction with correct QA outcome")


def test_failure_rate_reflects_bad_answers():
    from audit_log import log_interaction, failure_rate

    log_interaction("some unanswerable question", [], [], qa_passed=False, qa_notes=["no match"])
    rate = failure_rate(last_n=1)
    assert rate == 1.0
    print("PASS: failure_rate correctly reflects a failed QA outcome")


def test_freshness_check_flags_stale_rows():
    import sqlite3
    from db import get_conn
    from freshness_check import check

    conn = get_conn()
    conn.execute(
        "UPDATE faqs SET last_verified_date = '2020-01-01' WHERE id = 1"
    )
    conn.commit()
    conn.close()

    stale = check()
    assert any(r["id"] == 1 for r in stale)
    print("PASS: freshness check correctly flags a row verified in 2020")


if __name__ == "__main__":
    tmp_dir = setup_temp_db()
    try:
        test_audit_log_records_interaction()
        test_failure_rate_reflects_bad_answers()
        test_freshness_check_flags_stale_rows()
        print("\nAll audit/freshness tests passed.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
