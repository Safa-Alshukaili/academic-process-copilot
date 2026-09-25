"""
Question understanding + refusal, on the exact cases that motivated it.
run with: python demo/test_understanding.py
"""
import os
import sys
import shutil
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


def setup_temp_db():
    import db
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "institutional_processes.db")
    shutil.copy(db.DB_PATH, dst)
    db.DB_PATH = dst
    return tmp


def test_arabic_paraphrase_is_understood():
    # Previously "not found": the FAQ says "أُحرم", the student said "الحرمان".
    from agent import route_question, answer_question
    assert route_question("متى يصل الطالب للحرمان؟")["source"] == "faq:9"
    answer, _, qa_passed = answer_question("متى يصل الطالب للحرمان؟")
    assert "أقرب سؤال موثّق" in answer and "20%" in answer and qa_passed
    print("PASS: 'متى يصل الطالب للحرمان؟' answered from FAQ 9, with the matched question shown")


def test_ojt_credit_hours_is_refused():
    # Previously answered confidently from FAQ 3 (the wrong regulation).
    # The regulation sets no credit-hour threshold for OJT, so refusing is correct.
    from agent import route_question
    r = route_question("How many credit hours do I need before applying for OJT?")
    assert r["source"] is None, r
    print("PASS: the OJT credit-hour question is refused instead of answered from FAQ 3")


def test_citation_word_does_not_match_everything():
    # "المادة" means "course" to a student but appears in every answer's
    # "(المادة 24)" citation; citations are stripped before scoring.
    from text_normalize import tokens
    assert tokens("(المادة 24)", "ar") == []
    print("PASS: article citations are ignored when scoring")


def test_related_questions_listed():
    from agent import answer_question
    answer, _, _ = answer_question("Until when can I withdraw from a course?")
    assert "Related questions you can ask" in answer
    assert "How many courses can I withdraw from during my studies?" in answer
    print("PASS: sibling questions from the same process are listed")


if __name__ == "__main__":
    tmp = setup_temp_db()
    try:
        test_arabic_paraphrase_is_understood()
        test_ojt_credit_hours_is_refused()
        test_citation_word_does_not_match_everything()
        test_related_questions_listed()
        print("\nAll understanding tests passed.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
