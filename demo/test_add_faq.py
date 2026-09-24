"""
Regression test for the "closing the loop" flow: a question that fails
QA, gets added via add_faq.py, and then passes QA on the next ask —
without wiping any existing data. Run with:
python demo/test_add_faq.py

This specifically guards against a real bug found during development:
a FAQ with no linked process_id produced an answer with no "Verify
with" line, so it failed QA even when the answer was correct.
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


def test_closing_the_loop():
    from agent import answer_question
    from add_faq import add_faq
    from audit_log import recent

    question = "What is the library late fee for overdue books?"

    # 1. First ask: genuinely not in the database yet.
    _, _, qa_passed_before = answer_question(question)
    assert qa_passed_before is False, "expected this question to fail QA before it's added"

    # 2. Staff adds the verified answer — no process_id, matching a real
    # standalone FAQ (this is exactly what triggered the bug).
    add_faq(
        question=question,
        answer="The library charges 100 baisa per day per overdue book, capped at 5 OMR per item.",
        verified_by="Library Staff",
        process_id=None,
    )

    # 3. Same question, asked again: must now pass QA, and the answer
    # must actually include a "Verify with" line even with no process.
    answer_after, _, qa_passed_after = answer_question(question)
    assert qa_passed_after is True, "FAQ-only answer (no process) should pass QA after being added"
    assert "verify with" in answer_after.lower(), "answer must still include a Verify with line"
    assert "Library Staff" in answer_after

    # 4. Nothing got wiped: both the old failure and the new success are
    # still in the audit trail.
    questions_logged = [r["question"] for r in recent(1000)]
    assert questions_logged.count(question) == 2

    print("PASS: question fails QA, gets added via add_faq.py, then passes QA — nothing wiped")


if __name__ == "__main__":
    tmp_dir = setup_temp_db()
    try:
        test_closing_the_loop()
        print("\nAll closing-the-loop tests passed.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
