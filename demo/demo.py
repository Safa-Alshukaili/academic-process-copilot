"""
Runs both flows end to end with sample input, printing each stage so the
structured-prompting / retrieval / QA pipeline is visible, not a black box.

Run with:  python demo/demo.py
No API key required — runs in offline (template) mode by default.
Set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY to use a real model.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from agent import answer_question
from materials import draft_and_review


def line(char="-", n=70):
    print(char * n)


def demo_process_guidance():
    print("DEMO 1: Institutional process guidance agent")
    line()
    question = "How long is the mandatory training course?"
    print(f"Student question: {question}\n")

    answer, prompt, qa_passed = answer_question(question, role="student")

    print("Structured prompt sent to the model:")
    line(".")
    print(prompt)
    line(".")
    print("\nAgent answer:")
    print(answer)
    print(f"\nQA passed: {qa_passed}")
    print()


def demo_material_review():
    print("DEMO 2: AI-assisted academic material drafting + QA review")
    line()
    draft, qa_report, prompt = draft_and_review(
        topic="Introduction to Relational Databases",
        curriculum_requirements="Must align with CSSE-DB101 learning outcomes; "
                                  "target audience is first-year IT students.",
    )
    print("Draft:")
    print(draft)
    print("\nQA report (automated checks — human sign-off still required):")
    print(f"  Passed: {qa_report.passed}")
    for check, result in qa_report.checks.items():
        print(f"  - {check}: {'OK' if result else 'MISSING'}")
    for note in qa_report.notes:
        print(f"  Note: {note}")
    print()


if __name__ == "__main__":
    demo_process_guidance()
    line("=")
    demo_material_review()
