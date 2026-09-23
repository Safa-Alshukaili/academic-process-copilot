"""
Minimal tests for the QA layer — run with: python demo/test_qa_review.py
Shows the QA module catches a bad output, not just a good one.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from qa_review import review_process_guidance, review_academic_material


def test_flags_missing_verify_line():
    bad_answer = "You need 120 credit hours."
    report = review_process_guidance(bad_answer, context_used="PROCESS: OJT Registration...")
    assert report.passed is False
    assert "verify" in report.notes[0].lower()
    print("PASS: missing 'Verify with' line is correctly flagged")


def test_flags_ungrounded_answer():
    report = review_process_guidance(
        "You need 120 credit hours.\nVerify with: Registrar",
        context_used="No matching institutional data found.",
    )
    assert report.passed is False
    print("PASS: ungrounded (no-context) answer is correctly flagged")


def test_passes_good_answer():
    good = "You need 120 credit hours.\nVerify with: Career Guidance & Placement Office"
    report = review_process_guidance(good, context_used="PROCESS: OJT Registration...")
    assert report.passed is True
    print("PASS: well-formed, grounded answer passes QA")


def test_material_checklist():
    draft = "## Learning outcomes\n...\n## Assessment criteria\n..."
    report = review_academic_material(draft, ["Learning outcomes", "Assessment criteria", "Prerequisite knowledge"])
    assert report.passed is False
    assert any("Prerequisite" in n for n in report.notes)
    print("PASS: missing checklist item ('Prerequisite knowledge') is correctly flagged")


if __name__ == "__main__":
    test_flags_missing_verify_line()
    test_flags_ungrounded_answer()
    test_passes_good_answer()
    test_material_checklist()
    print("\nAll QA tests passed.")
