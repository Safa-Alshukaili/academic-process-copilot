"""
Retrieval layer for the RAG pipeline: BM25 (sparse, term-frequency based)
over the FAQ and process tables — now language-aware.

Bilingual design: this does NOT retrieve in one language and translate
the answer afterward. It detects which language the question was asked
in, then builds and scores a BM25 index over ONLY that language's text
(question_ar/answer_ar vs question/answer, etc.). Retrieval and
generation both run in the language actually asked — the same guarantee
the rest of the RAG pipeline gives for facts (see qa_review.py's
check_grounding) now also applies to language: an Arabic question can
only retrieve Arabic-scored matches, so it can't silently answer from an
English-only fact that happens to share no real relevance.

Why BM25 and not dense/embedding vectors: a dense retriever needs a
downloaded embedding model, which pulls in a real dependency and a
network call to a model host at index-build time. BM25 needs neither —
it's pure term statistics — while still fixing the real problems the
earlier word-loop retrieval had (see db.py's word-boundary fix): it
ranks by relevance instead of "any word matched", handles multi-word
queries properly, and is exactly what many production RAG systems use
as a first-stage retriever.

The index is rebuilt on every call rather than cached. At this dataset
size (tens of documents per language) that costs microseconds, and it
means a FAQ added via add_faq.py is retrievable immediately — no
separate reindex step to forget.
"""
import sys
import os
import re

sys.path.append(os.path.dirname(__file__))

from rank_bm25 import BM25Okapi
from db import get_conn, get_process_steps, get_forms

from text_normalize import tokens as _normalized_tokens

ARABIC_RANGE = r"\u0600-\u06FF"


def detect_language(text):
    """'ar' if the text contains any Arabic-script characters, else 'en'.
    A single Arabic word is enough to route the whole query to the
    Arabic corpus — mixed-script questions are rare in practice and this
    keeps the rule simple and auditable rather than trying to score
    per-word language mix."""
    return "ar" if re.search(f"[{ARABIC_RANGE}]", text) else "en"


def _tokenize(text, lang):
    """Normalization, light stemming, stopwords and the domain synonym
    table all live in text_normalize.py, applied identically to queries
    and documents."""
    return _normalized_tokens(text, lang)


def _load_documents(lang):
    """Returns a flat list of retrievable documents in the given
    language: one per FAQ, one per process. Each is
    (doc_type, record_id, text_for_scoring, record) — record always
    carries BOTH languages' columns (the renderer picks which to show),
    only the scoring text is language-specific."""
    conn = get_conn()
    cur = conn.cursor()

    docs = []
    q_col, a_col = ("question_ar", "answer_ar") if lang == "ar" else ("question", "answer")
    name_col, desc_col = ("name_ar", "description_ar") if lang == "ar" else ("name", "description")
    title_col, step_desc_col = ("title_ar", "description_ar") if lang == "ar" else ("title", "description")

    cur.execute("SELECT * FROM faqs")
    for r in cur.fetchall():
        r = dict(r)
        if lang == "ar" and (not r.get("question_ar") or not r.get("answer_ar")):
            # An FAQ added via add_faq.py without an Arabic translation
            # yet — correctly invisible to Arabic queries rather than
            # surfacing None/blank text or crashing the renderer.
            continue
        # The question is what a student's wording resembles most, so it
        # counts twice; the answer still contributes (numbers, terms).
        text = f"{r[q_col]} {r[q_col]} {r[a_col]}"
        docs.append(("faq", r["id"], text, r))

    cur.execute("SELECT * FROM processes")
    for r in cur.fetchall():
        r = dict(r)
        steps = get_process_steps(r["id"])
        step_text = " ".join(f"{s[title_col]} {s[step_desc_col]}" for s in steps)
        text = f"{r[name_col]} {r[desc_col]} {step_text}"
        docs.append(("process", r["id"], text, r))

    conn.close()
    return docs


def retrieve(query, language=None, top_k=5, min_score=0.1, min_shared_terms=2):
    """Ranks all FAQs and processes against the query with BM25, scored
    only against the query's own language, and returns the top-scoring
    ones above min_score. Returns (processes, faqs, language) — language
    is auto-detected unless explicitly passed, and the caller
    (agent.py) uses it to pick which columns to render and which prompt
    language to request.

    min_shared_terms guards against a real failure mode found while
    testing: a query entirely absent from the corpus can still score
    high on one document through a single coincidental rare-word match.
    Requiring at least min_shared_terms distinct query terms in a
    document — not just a high weighted score — filters that out."""
    language = language or detect_language(query)

    docs = _load_documents(language)
    if not docs:
        return [], [], language

    tokenized_corpus = [_tokenize(text, language) for (_, _, text, _) in docs]
    bm25 = BM25Okapi(tokenized_corpus)

    query_tokens = _tokenize(query, language)
    if not query_tokens:
        return [], [], language
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

    return processes, faqs, language


def retrieve_scored(query, language=None):
    """Scores every document and returns, for each one, the signals the
    confidence gate in agent.py needs — not just a rank:

      score     BM25 relevance
      shared    distinct query terms also present in the document
      coverage  shared / all distinct query terms (terms that appear
                nowhere in the data still count in the denominator, so
                "library late fee" can't look fully covered)
      anchor_ok the query's most specific known term (highest IDF, i.e.
                appearing in the fewest documents) is in this document

    Returns (candidates sorted by score, language, query_terms)."""
    import math

    language = language or detect_language(query)
    docs = _load_documents(language)
    query_terms = set(_tokenize(query, language))
    if not docs or not query_terms:
        return [], language, query_terms

    corpus = [_tokenize(text, language) for (_, _, text, _) in docs]
    doc_sets = [set(d) for d in corpus]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(list(query_terms))

    df = {t: sum(1 for d in doc_sets if t in d) for t in query_terms}
    known = [t for t in query_terms if df[t] > 0]
    anchor = min(known, key=lambda t: (df[t], t)) if known else None

    out = []
    for score, (doc_type, doc_id, _, record), terms in zip(scores, docs, doc_sets):
        shared = query_terms & terms
        out.append({
            "type": doc_type,
            "id": doc_id,
            "record": record,
            "score": float(score),
            "shared": len(shared),
            "coverage": len(shared) / len(query_terms),
            "anchor_ok": anchor is not None and anchor in terms,
        })
    out.sort(key=lambda c: c["score"], reverse=True)
    return out, language, query_terms
