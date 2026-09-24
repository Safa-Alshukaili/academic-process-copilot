"""
Test for kpi_summary() — run with: python demo/test_kpi.py

Confirms the aggregated view correctly reflects a realistic mix of
successful matches and gaps, not just that it returns without error.
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


def test_kpi_reflects_mixed_activity():
    from agent import answer_question
    from audit_log import kpi_summary

    # 2 real matches, 1 gap asked twice
    answer_question("What GPA puts me on academic probation?")
    answer_question("Until when can I withdraw from a course?")
    answer_question("What is the library late fee for overdue books?")
    answer_question("What is the library late fee for overdue books?")

    kpi = kpi_summary()

    assert kpi["total_questions_logged"] == 4
    assert kpi["qa_pass_rate_last_n"] == 0.5, f"expected 2/4 = 0.5, got {kpi['qa_pass_rate_last_n']}"
    assert len(kpi["top_unanswered_gaps"]) == 1
    assert kpi["top_unanswered_gaps"][0]["times_asked"] == 2
    assert kpi["total_faqs"] == 28
    assert kpi["total_processes"] == 14
    print("PASS: kpi_summary correctly reflects a mix of matches and repeated gaps")


if __name__ == "__main__":
    tmp_dir = setup_temp_db()
    try:
        test_kpi_reflects_mixed_activity()
        print("\nAll KPI tests passed.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
