import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.gap_grouping import group_questions, similarity

ITEMS = [
    {"question": "What is the library late fee?", "times_asked": 3, "last_asked": "2026-09-24"},
    {"question": "library late fee for overdue books", "times_asked": 1, "last_asked": "2026-09-25"},
    {"question": "كم رسوم تأخير الكتب في المكتبة؟", "times_asked": 1, "last_asked": "2026-09-23"},
    {"question": "كم رسوم التأخير في المكتبه", "times_asked": 2, "last_asked": "2026-09-25"},
    {"question": "What is the weather today?", "times_asked": 1, "last_asked": "2026-09-25"},
]

def test_similar_english_grouped():
    assert similarity(ITEMS[0]["question"], ITEMS[1]["question"]) >= 0.6

def test_similar_arabic_grouped_despite_spelling():
    assert similarity(ITEMS[2]["question"], ITEMS[3]["question"]) >= 0.6

def test_unrelated_not_grouped():
    assert similarity(ITEMS[0]["question"], ITEMS[4]["question"]) < 0.6

def test_one_off_question_filtered_out():
    groups = group_questions(ITEMS, min_total=2)
    reps = [g["representative"] for g in groups]
    assert "What is the weather today?" not in reps
    assert groups[0]["total_asked"] == 4  # 3 + 1 English variants

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
    for g in group_questions(ITEMS):
        print(g)
