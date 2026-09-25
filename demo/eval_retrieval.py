"""
Measures how often the agent picks the right source — or correctly refuses.

    python demo/eval_retrieval.py            # prints both sets
    python demo/eval_retrieval.py --ci       # also enforces minimum scores

Numbers per set:
  exact accuracy      : answered from exactly the expected FAQ/process
  right-topic rate    : answered from the expected FAQ OR a sibling in the
                        same process (e.g. "how many withdrawals" answered
                        with "withdrawal deadline"). The answer then also
                        lists the sibling questions, so the student can
                        re-ask — less harmful than a wrong topic, but still
                        not the answer they asked for.
  wrong-topic rate    : answered from an unrelated process — the dangerous one
  missed rate         : in-scope question refused (becomes a staff gap)
  false-answer rate   : out-of-scope question answered anyway (should refuse)
Wrong-topic and false-answer are the dangerous ones: a confident answer
from the wrong regulation. A refusal is logged as a gap and reaches the staff digest;
a wrong answer reaches nobody.
"""
import os
import sys
import shutil
import tempfile

HERE = os.path.dirname(__file__)
sys.path.append(os.path.join(HERE, "..", "src"))
sys.path.append(HERE)


def _isolate_db():
    """Run against a throwaway copy so evaluation never writes audit rows
    into the real database."""
    import db
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "institutional_processes.db")
    shutil.copy(db.DB_PATH, dst)
    db.DB_PATH = dst
    return tmp


def _topic_map():
    import db
    conn = db.get_conn()
    m = {f"faq:{r['id']}": r["process_id"] for r in conn.execute("SELECT id, process_id FROM faqs")}
    m.update({f"process:{r['id']}": r["id"] for r in conn.execute("SELECT id FROM processes")})
    conn.close()
    return m


def evaluate(items, decide):
    topic = _topic_map()
    right = sibling = wrong = refused_in = false_ans = refused_out = 0
    failures = []
    for q, expected in items:
        got = decide(q)
        if expected is None:
            if got is None:
                refused_out += 1
            else:
                false_ans += 1
                failures.append((q, expected, got))
        else:
            if got == expected:
                right += 1
            elif got is not None and topic.get(got) == topic.get(expected):
                sibling += 1
                failures.append((q, expected, got))
            elif got is None:
                refused_in += 1
                failures.append((q, expected, got))
            else:
                wrong += 1
                failures.append((q, expected, got))
    n_in = sum(1 for _, e in items if e is not None)
    n_out = len(items) - n_in
    return {
        "in_scope": n_in, "out_of_scope": n_out,
        "accuracy": right / n_in if n_in else 0.0,
        "right_topic_rate": (right + sibling) / n_in if n_in else 0.0,
        "wrong_answer_rate": wrong / n_in if n_in else 0.0,
        "missed_rate": refused_in / n_in if n_in else 0.0,
        "false_answer_rate": false_ans / n_out if n_out else 0.0,
        "failures": failures,
    }


def agent_decision(question):
    from agent import route_question
    return route_question(question)["source"]


def report(name, r):
    print(f"\n{name}: {r['in_scope']} in-scope, {r['out_of_scope']} out-of-scope")
    print(f"  exact accuracy      {r['accuracy']:.0%}")
    print(f"  right-topic rate    {r['right_topic_rate']:.0%}")
    print(f"  wrong-topic rate    {r['wrong_answer_rate']:.0%}")
    print(f"  missed (refused)    {r['missed_rate']:.0%}")
    print(f"  false-answer rate   {r['false_answer_rate']:.0%}")
    for q, exp, got in r["failures"]:
        print(f"    x {q!r}: expected {exp}, got {got}")


if __name__ == "__main__":
    from eval_questions import DEV, HELDOUT
    tmp = _isolate_db()
    try:
        dev = evaluate(DEV, agent_decision)
        held = evaluate(HELDOUT, agent_decision)
        report("DEV (used for tuning)", dev)
        report("HELDOUT (never used for tuning)", held)
        if "--ci" in sys.argv:
            # Regression floors, set at the values measured when the gate
            # was introduced (HELDOUT: 19/22 exact, 0/22 wrong-topic,
            # 2/12 false answers). The point is to fail loudly if a change
            # makes things worse, not to certify the system as "good".
            assert held["wrong_answer_rate"] <= 0.0, "an in-scope question was answered from an unrelated topic"
            assert held["false_answer_rate"] <= 2 / 12 + 1e-9, "more out-of-scope questions answered than before"
            assert held["accuracy"] >= 19 / 22 - 1e-9, "exact accuracy regressed"
            print("\nPASS: evaluation within regression floors")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
