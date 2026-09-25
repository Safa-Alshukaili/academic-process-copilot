"""
The LLM path must never put model-written text in front of a student.
run with: python demo/test_llm_selection.py

No real API call is made: agent._call_llm is replaced with a stub, so this
tests OUR handling of whatever the model returns — including a model that
ignores the instructions and tries to answer in prose.
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


def with_stub_llm(reply):
    import agent
    os.environ["LLM_PROVIDER"] = "anthropic"
    os.environ["ANTHROPIC_API_KEY"] = "test-not-a-real-key"
    agent._call_llm = lambda prompt: reply
    return agent


def test_selected_candidate_is_rendered_verbatim():
    agent = with_stub_llm("1")
    answer, _, qa_passed = agent.answer_question("What GPA puts me on academic probation?")
    assert "below 2.00" in answer and "Article 46" in answer, answer
    assert qa_passed
    print("PASS: a selected record is shown verbatim from the database")


def test_none_means_refusal():
    agent = with_stub_llm("NONE")
    answer, _, qa_passed = agent.answer_question("What GPA puts me on academic probation?")
    assert answer == agent.LABELS["en"]["not_found"], answer
    assert not qa_passed, "a refusal must be logged as a gap"
    print("PASS: NONE from the model becomes a refusal and a logged gap")


def test_prose_reply_is_never_shown():
    fabricated = "You need a GPA of 2.5 under Article 99."
    agent = with_stub_llm(fabricated)
    answer, _, _ = agent.answer_question("What GPA puts me on academic probation?")
    assert fabricated not in answer and "Article 99" not in answer
    assert answer == agent.LABELS["en"]["not_found"]
    print("PASS: a model that answers in prose is treated as NONE — its text never reaches the student")


def test_out_of_range_number_is_refusal():
    agent = with_stub_llm("7")
    answer, _, _ = agent.answer_question("What GPA puts me on academic probation?")
    assert answer == agent.LABELS["en"]["not_found"]
    print("PASS: an out-of-range candidate number is treated as NONE")


if __name__ == "__main__":
    tmp = setup_temp_db()
    try:
        test_selected_candidate_is_rendered_verbatim()
        test_none_means_refusal()
        test_prose_reply_is_never_shown()
        test_out_of_range_number_is_refusal()
        print("\nAll LLM-selection tests passed.")
    finally:
        os.environ.pop("LLM_PROVIDER", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        shutil.rmtree(tmp, ignore_errors=True)
