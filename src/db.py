import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "institutional_processes.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def find_process_by_keyword(keyword):
    """Naive keyword search over process names/descriptions and FAQs.
    A production version would use embeddings; this keeps the retrieval
    step transparent and auditable, which matters more for institutional
    QA/verification than search sophistication."""
    conn = get_conn()
    cur = conn.cursor()
    like = f"%{keyword.lower()}%"
    cur.execute(
        """
        SELECT * FROM processes
        WHERE lower(name) LIKE ? OR lower(description) LIKE ?
        """,
        (like, like),
    )
    processes = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT * FROM faqs
        WHERE lower(question) LIKE ? OR lower(answer) LIKE ?
        """,
        (like, like),
    )
    faqs = [dict(r) for r in cur.fetchall()]
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
