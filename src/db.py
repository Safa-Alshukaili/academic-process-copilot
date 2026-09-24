import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "institutional_processes.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _word_match(keyword, text):
    """Whole-word match, not substring — 'late' must not match inside
    'calculated' or 'later'. Found as a real bug: SQL LIKE '%late%' was
    matching unrelated FAQs through partial word overlap once the real
    UTAS regulation data (with denser vocabulary) replaced the sample
    data. Fetching rows and filtering here in Python (dataset is small)
    is simpler and more correct than fighting LIKE for word boundaries."""
    return re.search(r"\b" + re.escape(keyword.lower()) + r"\b", text.lower()) is not None


def find_process_by_keyword(keyword):
    """Whole-word keyword search over process names/descriptions and FAQs.
    A production version would use embeddings; this keeps the retrieval
    step transparent and auditable, which matters more for institutional
    QA/verification than search sophistication."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM processes")
    processes = [dict(r) for r in cur.fetchall()
                 if _word_match(keyword, r["name"]) or _word_match(keyword, r["description"])]

    cur.execute("SELECT * FROM faqs")
    faqs = [dict(r) for r in cur.fetchall()
            if _word_match(keyword, r["question"]) or _word_match(keyword, r["answer"])]
    conn.close()
    return processes, faqs


def get_process_steps(process_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM process_steps WHERE process_id = ? ORDER BY step_number",
        (process_id,),
    )
    steps = [dict(r) for r in cur.fetchall()]
    conn.close()
    return steps


def get_forms(process_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM forms WHERE process_id = ?", (process_id,))
    forms = [dict(r) for r in cur.fetchall()]
    conn.close()
    return forms
