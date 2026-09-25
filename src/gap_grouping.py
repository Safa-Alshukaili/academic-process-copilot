"""Group similar unanswered questions so staff see one gap, not ten phrasings of it.

Input: the list that /admin/unanswered already returns
       [{"question": str, "times_asked": int, "last_asked": str}, ...]
Output: groups sorted by total times asked, most-asked first.

Similarity is lexical (shared words after normalization), not semantic:
"رسوم المكتبة" and "غرامة تأخير الكتب" will NOT be grouped together.
"""
import re
from difflib import SequenceMatcher

_TASHKEEL = re.compile(r"[\u064B-\u0652\u0640]")  # diacritics + tatweel
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)

_STOPWORDS = {
    # English
    "what", "how", "is", "are", "the", "a", "an", "do", "does", "i", "my", "me",
    "can", "to", "of", "for", "in", "on", "at", "if", "when", "where", "which",
    # Arabic (after normalization)
    "ما", "ماذا", "كيف", "هل", "كم", "متي", "اين", "في", "علي", "من", "الي",
    "عن", "انا", "اذا", "لو", "هو", "هي", "ايش", "وش", "شو", "يعني",
}


def normalize(text: str) -> str:
    t = text.lower()
    t = _TASHKEEL.sub("", t)
    t = re.sub("[أإآ]", "ا", t)
    t = t.replace("ة", "ه").replace("ى", "ي")
    t = _PUNCT.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(text: str) -> set:
    out = set()
    for w in normalize(text).split():
        if w.startswith("ال") and len(w) > 4:  # الرسوم -> رسوم
            w = w[2:]
        if w not in _STOPWORDS and len(w) > 1:
            out.add(w)
    return out


def similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    jaccard = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    seq = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return max(jaccard, seq)


def group_questions(items: list, threshold: float = 0.6, min_total: int = 2) -> list:
    """Greedy clustering: each question joins the first group whose
    representative (most-asked member) is similar enough, else starts a new one.
    Only groups asked at least `min_total` times in total are returned."""
    groups = []
    for item in sorted(items, key=lambda x: x.get("times_asked", 1), reverse=True):
        for g in groups:
            if similarity(item["question"], g["representative"]) >= threshold:
                g["variants"].append(item["question"])
                g["total_asked"] += item.get("times_asked", 1)
                g["last_asked"] = max(g["last_asked"], item.get("last_asked", ""))
                break
        else:
            groups.append({
                "representative": item["question"],
                "variants": [item["question"]],
                "total_asked": item.get("times_asked", 1),
                "last_asked": item.get("last_asked", ""),
            })
    result = [g for g in groups if g["total_asked"] >= min_total]
    return sorted(result, key=lambda g: g["total_asked"], reverse=True)
