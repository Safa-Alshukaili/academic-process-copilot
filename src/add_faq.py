"""
Closes the loop on a question the agent couldn't answer: adds it as a
new, verified FAQ row WITHOUT wiping the existing database (unlike
data/seed.py, which rebuilds everything from scratch and would also
erase audit_log history — never run seed.py to add one answer).

This is the human-sign-off step documented in docs/QA_PROCESS.md,
made concrete: a staff member reviews an unanswered question (surfaced
by GET /admin/unanswered or src/freshness_check.py's counterpart),
confirms the correct answer against the real source, and runs this to
publish it. Every student who asks the same question afterward gets it
automatically from the agent instead of hitting the same gap again.

Bilingual: the Arabic question/answer are optional. If you skip them,
the FAQ is added and immediately answers English questions — it simply
won't surface for Arabic queries (src/retrieval.py excludes FAQs with
no Arabic translation from the Arabic corpus, rather than showing a
blank/English-only answer to an Arabic question). Add the Arabic fields
later with the same command and it becomes retrievable in both
languages from then on.

Usage:
    python src/add_faq.py

    python src/add_faq.py --question "..." --answer "..." \
        --verified-by "Registrar" --process-id 2 \
        --question-ar "..." --answer-ar "..."
"""
import sys
import os
import argparse
import datetime

sys.path.append(os.path.dirname(__file__))
from db import get_conn

VERIFIED_BY_AR_DEFAULT = None  # left untranslated unless explicitly given


def add_faq(question, answer, verified_by, process_id=None, verified_date=None,
            question_ar=None, answer_ar=None, verified_by_ar=None):
    verified_date = verified_date or datetime.date.today().isoformat()
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO faqs (process_id, question, answer, last_verified_date, verified_by, "
        "question_ar, answer_ar, verified_by_ar) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (process_id, question, answer, verified_date, verified_by,
         question_ar, answer_ar, verified_by_ar or (verified_by if question_ar else None)),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_processes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, name_ar FROM processes ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _interactive():
    print("Add a verified FAQ (closes a gap surfaced by GET /admin/unanswered)\n")
    question = input("Question exactly as students ask it (English): ").strip()
    answer = input("Verified answer (English): ").strip()
    verified_by = input("Verified by (name or role, e.g. 'Registrar'): ").strip()

    print("\nArabic translation (optional — leave blank to skip for now;")
    print("the FAQ will only answer English questions until you add it):")
    question_ar = input("Question (Arabic): ").strip() or None
    answer_ar = input("Answer (Arabic): ").strip() or None

    processes = list_processes()
    print("\nLink to an existing process? (optional — leave blank for none)")
    for p in processes:
        print(f"  [{p['id']}] {p['name']} / {p['name_ar']}")
    pid_raw = input("Process id (or blank): ").strip()
    process_id = int(pid_raw) if pid_raw else None

    if not question or not answer or not verified_by:
        print("\nQuestion, answer, and verified-by are all required. Nothing added.")
        return

    new_id = add_faq(question, answer, verified_by, process_id,
                      question_ar=question_ar, answer_ar=answer_ar)
    print(f"\nAdded FAQ #{new_id}. It will show up for this question — and any "
          f"question matching its keywords — the next time the agent runs."
          + ("" if question_ar else " (English only until you add the Arabic translation.)"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question")
    parser.add_argument("--answer")
    parser.add_argument("--verified-by")
    parser.add_argument("--process-id", type=int, default=None)
    parser.add_argument("--question-ar", default=None)
    parser.add_argument("--answer-ar", default=None)
    args = parser.parse_args()

    if args.question and args.answer and args.verified_by:
        new_id = add_faq(args.question, args.answer, args.verified_by, args.process_id,
                          question_ar=args.question_ar, answer_ar=args.answer_ar)
        print(f"Added FAQ #{new_id}.")
    else:
        _interactive()
