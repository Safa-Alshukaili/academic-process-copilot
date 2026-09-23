"""
Flags FAQ rows not re-verified within the freshness window (default 6
months). Implements the "Next steps" item named explicitly in
docs/QA_PROCESS.md — an institutional agent is only as trustworthy as
its underlying data is current.

Run with: python src/freshness_check.py
"""
import sys
import os
import datetime

sys.path.append(os.path.dirname(__file__))
from db import get_conn

FRESHNESS_DAYS = 180


def check(days=FRESHNESS_DAYS):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM faqs")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    stale = []
    for r in rows:
        verified = datetime.date.fromisoformat(r["last_verified_date"])
        if verified < cutoff:
            stale.append(r)
    return stale


if __name__ == "__main__":
    stale = check()
    if not stale:
        print(f"All FAQ rows verified within the last {FRESHNESS_DAYS} days.")
    else:
        print(f"{len(stale)} FAQ row(s) need re-verification (older than {FRESHNESS_DAYS} days):")
        for r in stale:
            print(f"  [{r['id']}] \"{r['question']}\" — last verified {r['last_verified_date']} by {r['verified_by']}")
