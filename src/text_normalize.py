"""
Text normalization, light stemming and a small domain synonym table —
the "understand the question" half of retrieval, without an embedding
model.

Why this exists: BM25 only matches identical tokens. Before this module,
"متى يصل الطالب للحرمان؟" returned "not found" even though FAQ 9 answers
it, because the FAQ says "أُحرم" and the student said "الحرمان"; and
"كم أعلى ساعات أسجلها بالفصل؟" missed FAQ 1 because of "أعلى" vs "أقصى"
and "ساعات" vs "ساعة". Three layers fix most of that:

1. normalize()  — orthography: diacritics, tatweel, alef/ya/ta-marbuta
                  variants, lowercase.
2. stem()       — strips common Arabic prefixes/suffixes (ال، و، ب، ات،
                  ين، ـه ...) and simple English inflections (-s, -ed, -ing),
                  so "ساعات"/"ساعة" and "hours"/"hour" become one token.
3. CONCEPTS     — a hand-written table mapping words that mean the same
                  thing in THIS domain to one concept token: "postpone",
                  "defer" -> #defer ; "الحرمان"، "انحرم"، "محروم" -> #barred.

Trade-off, stated plainly: the synonym table is curated, not learned. It
covers the vocabulary of the 14 processes / 28 FAQs and the phrasings in
demo/eval_questions.py's DEV set. Words nobody thought of still miss —
that is what demo/eval_retrieval.py's HELDOUT set measures, and what an
embedding model would improve. Adding a FAQ in a new topic may need a
line added here.
"""
import re

ARABIC = r"\u0600-\u06FF"
_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")

# Citations like "(المادة 24)" / "(Article 24)" appear in every answer.
# They are removed before scoring so "المادة" (which students use to mean
# "course") doesn't match every document through its citation.
_CITATION = re.compile(r"\(?\s*(?:المادة|المادتان|Article|Art\.)\s*\d+[^)]*\)?", re.IGNORECASE)


def normalize(text):
    t = _CITATION.sub(" ", text)
    t = _TASHKEEL.sub("", t.lower())
    t = re.sub(r"[\u060C\u061B\u061F\u066A-\u066D\u06D4]", " ", t)  # Arabic punctuation
    t = re.sub("[أإآٱ]", "ا", t)
    return t.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")


_AR_PREFIXES = ("وبال", "وال", "بال", "فال", "كال", "لل", "ال")
_AR_SUFFIXES = ("ات", "ين", "ون", "ها", "هم", "كم", "نا", "ه", "ي", "ك")


def stem(word, lang):
    if lang == "ar":
        for p in _AR_PREFIXES:
            if word.startswith(p) and len(word) - len(p) >= 3:
                word = word[len(p):]
                break
        else:
            if word.startswith("و") and len(word) >= 5:
                word = word[1:]
        for _ in range(2):  # at most two stacked suffixes: النهائية -> نهايي -> نهاي
            for s in _AR_SUFFIXES:
                if word.endswith(s) and len(word) - len(s) >= 3:
                    word = word[: -len(s)]
                    break
            else:
                break
        # ta marbuta before a possessive suffix: دراستي -> دراست -> دراس
        if word.endswith("ت") and len(word) >= 5:
            word = word[:-1]
        return word
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


# concept -> surface words, per language. Written in plain spelling;
# they are normalized and stemmed exactly like the text they match.
CONCEPTS = {
    "en": {
        "#withdraw": ["withdraw", "withdrawal", "withdrew", "withdrawing"],
        "#defer": ["defer", "deferral", "deferring", "postpone", "postponement", "postponing"],
        "#stipend": ["stipend", "allowance", "subsistence"],
        "#training": ["training", "ojt", "internship"],
        "#major": ["major", "specialization", "specialisation"],
        "#barred": ["barred", "banned", "bar", "deprived"],
        "#appeal": ["appeal", "grievance", "contest"],
        "#repeat": ["repeat", "retake", "redo", "repeated"],
        "#return": ["rejoin", "re-enroll", "reenroll", "return", "back"],
        "#graduate": ["graduate", "graduation", "graduating"],
        "#gpa": ["gpa", "cgpa", "lcgpa", "average"],
        "#course": ["course", "subject", "class", "module"],
        "#max": ["maximum", "max", "most", "highest", "upper"],
        "#min": ["minimum", "min", "least", "lowest", "fewest"],
        "#semester": ["semester", "term"],
        "#exam": ["exam", "examination", "test"],
        "#deadline": ["deadline", "last", "latest", "until"],
        "#transfer": ["transfer", "move", "moving", "switch"],
        "#grade": ["grade", "mark", "result"],
        "#day": ["day", "days"],
    },
    "ar": {
        "#barred": ["حرمان", "الحرمان", "احرم", "أحرم", "انحرم", "أنحرم", "ينحرم", "محروم", "يحرم", "حرم"],
        "#absence": ["غياب", "الغياب", "غبت", "اغيب", "تغيب", "غايب", "تغيّب"],
        "#withdraw": ["انسحاب", "الانسحاب", "انسحب", "أنسحب", "منسحب"],
        "#defer": ["تأجيل", "التأجيل", "أأجل", "أأجّل", "اأجل", "أجل", "مؤجل", "أؤجل"],
        "#stipend": ["مخصصات", "المخصصات", "الإعاشة", "إعاشة", "مكافأة", "المكافأة", "مكافاة"],
        "#training": ["تدريب", "التدريب"],
        "#major": ["تخصص", "تخصصي", "التخصص"],
        "#appeal": ["تظلم", "التظلم", "اعتراض", "أعترض", "استئناف"],
        "#repeat": ["إعادة", "أعيد", "اعيد", "المعادة", "معادة", "المعاده"],
        "#return": ["أرجع", "ارجع", "العودة", "عودة", "رجوع", "أعود", "اعود", "إعادة القيد"],
        "#graduate": ["تخرج", "التخرج", "أتخرج", "اتخرج"],
        "#gpa": ["معدل", "المعدل", "معدلي"],
        "#course": ["مقرر", "مقررات", "المقرر", "مادة", "المادة", "مواد"],
        "#max": ["أقصى", "اقصى", "أعلى", "اعلى", "أكبر"],
        "#min": ["أقل", "اقل", "أدنى", "ادنى"],
        "#semester": ["فصل", "الفصل", "فصول", "ترم", "سمستر"],
        "#exam": ["اختبار", "الاختبار", "امتحان", "الامتحان"],
        "#transfer": ["انتقل", "أنتقل", "انتقال", "الانتقال", "تحويل", "أحول"],
        "#grade": ["درجة", "الدرجة", "تقدير", "التقدير", "علامة", "نتيجة"],
        "#day": ["يوم", "أيام", "ايام"],
        "#hour": ["ساعة", "ساعات", "الساعات"],
    },
}

STOPWORDS = {
    "en": {
        "how", "many", "what", "when", "where", "does", "do", "the", "for", "need",
        "with", "from", "have", "this", "that", "your", "you", "can", "will",
        "into", "after", "about", "is", "are", "a", "an", "of", "to", "in", "on",
        "my", "me", "i", "if", "it", "am", "be", "there", "any", "get", "still",
        "allowed", "possible", "much", "which", "should", "now", "what's", "s",
        "one", "total", "required", "number", "before", "whole", "student", "students",
    },
    "ar": {
        "هل", "كم", "متى", "اي", "أي", "ما", "ماذا", "من", "الى", "إلى", "في",
        "على", "عن", "مع", "او", "أو", "ثم", "قد", "لا", "هذا", "هذه", "ذلك",
        "التي", "الذي", "بعد", "قبل", "انا", "أنا", "انت", "أنت", "احتاج",
        "أحتاج", "اقدر", "أقدر", "لازم", "يجب", "كيف", "وش", "ايش", "شو", "يصير",
        "اذا", "إذا", "لو", "عشان", "ابغى", "أبغى", "ابي", "أبي", "اللي", "الي",
        "يعني", "فيه", "هو", "هي", "عندي", "يسمح", "مرة", "مره", "يصل", "وأنا",
        "وانا", "المطلوب", "مطلوب", "عدد", "آخر", "اخر", "فيها", "فيه", "بس", "طالب", "الطالب", "طلاب",
    },
}


def _build_lookup():
    lookup, stops = {}, {}
    for lang in ("en", "ar"):
        stops[lang] = {stem(normalize(w), lang) for w in STOPWORDS[lang]} | {normalize(w) for w in STOPWORDS[lang]}
        lookup[lang] = {}
        for concept, words in CONCEPTS[lang].items():
            for w in words:
                for part in _split(normalize(w), lang):
                    lookup[lang][stem(part, lang)] = concept
    return lookup, stops


def _split(text, lang):
    if lang == "ar":
        return re.findall(f"[{ARABIC}]+", text)
    return re.findall(r"[a-z0-9]+(?:\.\d+)?", text)


_LOOKUP, _STOPS = _build_lookup()


def tokens(text, lang):
    """normalize -> split -> drop stopwords -> stem -> map to concept.
    Used identically for queries and for documents, so both sides land on
    the same vocabulary."""
    out = []
    for w in _split(normalize(text), lang):
        if w in _STOPS[lang] or len(w) < 2:
            continue
        s = stem(w, lang)
        if s in _STOPS[lang] or len(s) < 2:
            continue
        out.append(_LOOKUP[lang].get(s, s))
    return out
