"""
Retrieval layer for the RAG pipeline: BM25 (sparse, term-frequency based)
over the FAQ and process tables.

Why BM25 and not dense/embedding vectors: a dense retriever needs a
downloaded embedding model, which pulls in a real dependency and a
network call to a model host at index-build time. BM25 needs neither —
it's pure term statistics — while still fixing the real problems the
earlier word-loop retrieval had (see db.py's word-boundary fix): it
ranks by relevance instead of "any word matched", handles multi-word
queries properly, and is exactly what many production RAG systems use
as a first-stage retriever (often ahead of a reranker), not a toy
substitute for "real" retrieval.

The index is rebuilt on every call rather than cached. At this dataset
size (tens of documents) that costs microseconds, and it means a FAQ
added via add_faq.py is retrievable immediately — no separate reindex
step to forget.
"""
import sys
import os
import re

sys.path.append(os.path.dirname(__file__))

from rank_bm25 import BM25Okapi
from db import get_conn, get_process_steps, get_forms

STOPWORDS = {
    "how", "many", "what", "when", "where", "does", "do", "the", "for",
    "before", "applying", "apply", "need", "with", "from", "have", "this",
    "that", "your", "you", "can", "will", "into", "after", "about", "is",
    "are", "a", "an", "of", "to", "in", "on", "my", "me", "i",
}


def _tokenize(text):
    words = re.findall(r"[a-z0-9]+(?:\.\d+)?", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def _load_documents():
    """Returns a flat list of retrievable documents: one per FAQ, one per
    process. Each is (doc_type, record_id, text_for_scoring, record)."""
    conn = get_conn()
    cur = conn.cursor()

    docs = []

    cur.execute("SELECT * FROM faqs")
    for r in cur.fetchall():
        r = dict(r)
        text = f"{r['question']} {r['answer']}"
        docs.append(("faq", r["id"], text, r))

    cur.execute("SELECT * FROM processes")
    for r in cur.fetchall():
        r = dict(r)
        steps = get_process_steps(r["id"])
        step_text = " ".join(f"{s['title']} {s['description']}" for s in steps)
        text = f"{r['name']} {r['description']} {step_text}"
        docs.append(("process", r["id"], text, r))

    conn.close()
    return docs


def retrieve(query, top_k=5, min_score=0.1, min_shared_terms=2):
    """Ranks all FAQs and processes against the query with BM25 and
    returns the top-scoring ones above min_score. Returns
    (processes, faqs) in the same shape agent.py already expects, so
    this is a drop-in replacement for the old per-keyword loop — just a
    properly ranked one instead of an "any word matched" one.

    min_shared_terms guards against a real failure mode found while
    testing: a query entirely absent from the corpus can still score
    high on one document through a single coincidental rare-word match
    (e.g. "library late fee for overdue books" scored 'Final Grade
    Appeal' highly purely because that process mentions "no fee" once —
    a rare term gets a large BM25 weight even as a single hit). Requiring
    at least min_shared_terms distinct query terms in a document — not
    just a high weighted score — filters that out without needing a
    smarter (and heavier) retriever."""
    docs = _load_documents()
    if not docs:
        return [], []

    tokenized_corpus = [_tokenize(text) for (_, _, text, _) in docs]
    bm25 = BM25Okapi(tokenized_corpus)

    query_tokens = _tokenize(query)
    if not query_tokens:
        return [], []
    query_token_set = set(query_tokens)
    effective_min_shared = min(min_shared_terms, len(query_token_set))

    scores = bm25.get_scores(query_tokens)

    candidates = []
    for score, doc, doc_tokens in zip(scores, docs, tokenized_corpus):
        if score < min_score:
            continue
        shared = query_token_set & set(doc_tokens)
        if len(shared) < effective_min_shared:
            continue
        candidates.append((score, doc))

    ranked = sorted(candidates, key=lambda x: x[0], reverse=True)[:top_k]

    processes, faqs = [], []
    seen_process_ids = set()
    for score, (doc_type, doc_id, _, record) in ranked:
        if doc_type == "faq":
            faqs.append(record)
        elif doc_type == "process" and doc_id not in seen_process_ids:
            processes.append(record)
            seen_process_ids.add(doc_id)

    return processes, faqs
