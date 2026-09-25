"""
Labeled evaluation questions for retrieval + answer/refuse decisions.

Each entry: (question, expected)
  expected = "faq:<id>"      -> the FAQ that actually answers it
             "process:<id>"  -> no FAQ covers it, but a process does
             None            -> NOT in the data; the correct behaviour is to refuse

Two separate sets, on purpose:
  DEV      -> used while tuning normalization, the synonym table and the
              confidence gate. Scores on this set are optimistic by design.
  HELDOUT  -> written BEFORE any tuning and never edited afterwards. This is
              the honest number. Both sets were written by the project
              author, not collected from real students, so even HELDOUT is
              an approximation of real traffic, not a substitute for it.
"""

DEV = [
    # --- in scope, English, reworded away from the FAQ text ---
    ("What's the most credit hours I can take in one semester?", "faq:1"),
    ("Least number of hours I must register as a full-time student?", "faq:2"),
    ("Is it possible to take 21 credit hours?", "faq:3"),
    ("What is the last week I can withdraw from a course?", "faq:5"),
    ("How many courses am I allowed to withdraw from in total?", "faq:6"),
    ("What happens if I exceed 20% absence in a course?", "faq:8"),
    ("At what absence percentage do I get a warning?", "faq:9"),
    ("How many semesters can I postpone my studies?", "faq:10"),
    ("Do I still get my allowance if I defer?", "faq:11"),
    ("Last week to submit a deferral request?", "faq:12"),
    ("What GPA causes academic probation?", "faq:13"),
    ("How many semesters to get out of probation?", "faq:14"),
    ("How long is the OJT?", "faq:16"),
    ("Minimum CGPA required for graduation?", "faq:18"),
    ("Can I repeat a course to raise my GPA?", "faq:19"),
    ("Deadline to appeal my final grade?", "faq:21"),
    ("I missed the final exam with a medical excuse, what happens?", "faq:22"),
    ("Can I change my major?", "faq:25"),
    ("Can I come back to the university after I withdrew?", "faq:26"),
    ("Maximum years to finish a diploma?", "faq:27"),
    # --- in scope, Arabic, reworded ---
    ("متى يصل الطالب للحرمان؟", "faq:9"),
    ("كم أعلى ساعات أسجلها بالفصل؟", "faq:1"),
    ("كم أقل ساعات لازم أسجل؟", "faq:2"),
    ("آخر أسبوع للانسحاب من المادة؟", "faq:5"),
    ("كم مرة أقدر أنسحب من مقررات؟", "faq:6"),
    ("اذا غبت اكثر من 20 بالمية وش يصير؟", "faq:8"),
    ("كم فصل أقدر أأجل الدراسة؟", "faq:10"),
    ("هل تنصرف المخصصات وأنا مؤجل؟", "faq:11"),
    ("كم المعدل اللي يدخلني الملاحظة الأكاديمية؟", "faq:13"),
    ("كم مدة التدريب العملي؟", "faq:16"),
    ("كم المعدل المطلوب للتخرج؟", "faq:18"),
    ("أبغى أعيد مادة نجحت فيها عشان أرفع معدلي", "faq:19"),
    ("كم يوم عندي للتظلم على الدرجة النهائية؟", "faq:21"),
    ("غبت عن الامتحان النهائي بعذر مقبول", "faq:22"),
    ("أبغى أغير تخصصي كم مرة يسمح؟", "faq:25"),
    # --- out of scope: correct behaviour is to refuse ---
    ("How many credit hours do I need before applying for OJT?", None),
    ("What is the library late fee for overdue books?", None),
    ("What is the weather today?", None),
    ("How much is the parking permit?", None),
    ("Where is the cafeteria?", None),
    ("كم رسوم تأخير الكتب في المكتبة؟", None),
    ("وين مواقف السيارات؟", None),
    ("كم سعر الوجبة في الكافتيريا؟", None),
    ("متى يبدأ الدوام في رمضان؟", None),
]

HELDOUT = [
    # --- in scope, English ---
    ("Max course load for spring?", "faq:1"),
    ("If my semester GPA was 3.6 can I register extra hours?", "faq:3"),
    ("Is there a minimum number of students for a course to open?", "faq:4"),
    ("After I withdraw, how low can my registered hours go?", "faq:7"),
    ("When am I barred from the final exam because of absences?", "faq:9"),
    ("Is there a deadline for requesting to postpone my study?", "faq:12"),
    ("How many hours can I take while I'm on probation?", "faq:15"),
    ("Does the internship period count in my study duration?", "faq:17"),
    ("Do repeated courses affect my GPA?", "faq:20"),
    ("My excuse for missing the final was rejected, what now?", "faq:23"),
    ("How do I move to another UTAS branch?", "faq:24"),
    ("Maximum time to complete a bachelor degree?", "faq:28"),
    # --- in scope, Arabic ---
    ("هل أقدر أسجل 21 ساعة؟", "faq:3"),
    ("كم طالب لازم يسجل عشان تنفتح المادة؟", "faq:4"),
    ("متى أنحرم من الاختبار النهائي؟", "faq:9"),
    ("آخر موعد لطلب تأجيل الفصل؟", "faq:12"),
    ("كم فصل عندي عشان أطلع من الإنذار الأكاديمي؟", "faq:14"),
    ("هل فترة التدريب تنحسب من مدة الدراسة؟", "faq:17"),
    ("هل المادة المعادة تنحسب في المعدل؟", "faq:20"),
    ("رفضوا عذري عن الاختبار النهائي وش يصير؟", "faq:23"),
    ("أبغى أنتقل لفرع ثاني", "faq:24"),
    ("كم أقصى مدة للبكالوريوس؟", "faq:28"),
    # --- out of scope ---
    ("How do I reset my student email password?", None),
    ("What are the library opening hours?", None),
    ("How much are the tuition fees for international students?", None),
    ("Can I bring a guest to the graduation ceremony?", None),
    ("Is there a shuttle bus between campuses?", None),
    ("How many credit hours do I need to start my graduation project?", None),
    ("كيف أغير كلمة مرور الايميل الجامعي؟", None),
    ("متى تفتح المكتبة؟", None),
    ("كم رسوم السكن الجامعي؟", None),
    ("هل فيه باص بين الفروع؟", None),
    ("كم ساعة لازم أخلص قبل مشروع التخرج؟", None),
    ("كيف أطبع في المختبر؟", None),
]
