"""
Bilingual regression tests — run with: python demo/test_bilingual.py

Confirms the core bilingual guarantee: a question asked in Arabic is
retrieved and answered in Arabic (not translated after the fact), an
English question stays in English, and the two don't cross-contaminate.
Also covers the real bug found while building this: a process correctly
identified via a matched FAQ's process_id, but not itself present in the
initial BM25 candidate list, used to be silently left as a wrong,
loosely-matched process instead of being fetched directly.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from retrieval import detect_language


def test_language_detection():
    assert detect_language("What GPA puts me on academic probation?") == "en"
    assert detect_language("أي معدل يخليني تحت الملاحظة الأكاديمية؟") == "ar"
    assert detect_language("Registration Article 24") == "en"
    print("PASS: language detection correctly distinguishes English and Arabic questions")


def test_arabic_question_gets_arabic_answer():
    from agent import answer_question
    answer, prompt, qa_passed = answer_question("أي معدل يخليني تحت الملاحظة الأكاديمية؟")
    assert qa_passed is True
    assert detect_language(answer) == "ar", "answer should be in Arabic for an Arabic question"
    assert "2.00" in answer  # the actual GPA threshold, Article 46
    assert "تحقق مع" in answer, "Arabic answers must use the Arabic verify-line label"
    print("PASS: Arabic question retrieves and answers in Arabic, with the right fact")


def test_english_question_gets_english_answer():
    from agent import answer_question
    answer, prompt, qa_passed = answer_question("What GPA puts me on academic probation?")
    assert qa_passed is True
    assert "Verify with" in answer
    assert "تحقق مع" not in answer, "an English answer must not leak Arabic labels"
    print("PASS: English question retrieves and answers in English, unaffected by Arabic data")


def test_process_narrowing_fetches_correct_process_even_if_not_in_candidates():
    """Regression test for a real bug: the Arabic probation query's top
    FAQ correctly points at the Academic Probation process (id 6), but
    that process didn't itself score into the initial BM25 candidate
    list — 'Course Withdrawal' did, coincidentally, on shared terms. The
    old narrowing logic only filtered existing candidates and silently
    kept the wrong one when the right one wasn't among them."""
    from agent import answer_question
    answer, prompt, qa_passed = answer_question("أي معدل يخليني تحت الملاحظة الأكاديمية؟")
    assert "الملاحظة الأكاديمية" in answer, "must reference Academic Probation, not an unrelated process"
    assert "الانسحاب" not in answer.split("تحقق مع")[0], "must not reference Course Withdrawal instead"
    print("PASS: process narrowing fetches the correct process even when it wasn't in the initial candidates")


def test_arabic_query_with_no_match_escalates_in_arabic():
    from agent import answer_question
    answer, prompt, qa_passed = answer_question("ما هو رسوم تأخير الكتب بالمكتبة؟")
    assert qa_passed is False
    assert detect_language(answer) == "ar"
    print("PASS: an Arabic question outside the data escalates in Arabic, not English")


if __name__ == "__main__":
    test_language_detection()
    test_arabic_question_gets_arabic_answer()
    test_english_question_gets_english_answer()
    test_process_narrowing_fetches_correct_process_even_if_not_in_candidates()
    test_arabic_query_with_no_match_escalates_in_arabic()
    print("\nAll bilingual tests passed.")
