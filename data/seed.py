"""
Builds institutional_processes.db from the real, published UTAS Academic
Regulation (Decision No. 612/2022, Official Gazette No. 1468). Every
process, step and FAQ is bilingual (English + Arabic) sourced from the
same articles, so a student can ask in either language and get an answer
in that language — not a translated-after-the-fact answer, but retrieval
and generation both running against the language actually asked in.

Coverage note: this is a curated set of the most commonly-asked
regulations, not a verbatim reproduction of all 92 articles — see the
note at the top of the English-only version of this file in earlier
project history for why a Q&A agent works this way.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "institutional_processes.db")
SOURCE_EN = "UTAS Academic Regulation (Decision 612/2022)"
SOURCE_AR = "النظام الأكاديمي لجامعة التقنية والعلوم التطبيقية (قرار 612/2022)"
VERIFIED_DATE = "2026-09-24"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stakeholders (
    id INTEGER PRIMARY KEY,
    role TEXT NOT NULL CHECK(role IN ('student','advisor','staff','department_head')),
    department TEXT,
    program TEXT
);

CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    applies_to_role TEXT NOT NULL,
    responsible_office TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    description_ar TEXT NOT NULL,
    responsible_office_ar TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS process_steps (
    id INTEGER PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id),
    step_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    required_documents TEXT,
    title_ar TEXT NOT NULL,
    description_ar TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forms (
    id INTEGER PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id),
    form_name TEXT NOT NULL,
    form_location TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY,
    process_id INTEGER REFERENCES processes(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    last_verified_date TEXT NOT NULL,
    verified_by TEXT NOT NULL,
    question_ar TEXT,
    answer_ar TEXT,
    verified_by_ar TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    question TEXT NOT NULL,
    matched_process_ids TEXT,
    matched_faq_ids TEXT,
    qa_passed INTEGER NOT NULL,
    qa_notes TEXT,
    language TEXT
);
"""

# id, name, description, role, office, name_ar, description_ar, office_ar
PROCESSES = [
    (1, "Course Registration and Load", "Registering for courses each semester within the allowed credit-hour load.", "student", "Admissions and Registration Deanship",
        "التسجيل في المقررات والعبء الدراسي", "تسجيل المقررات الدراسية كل فصل ضمن العبء الدراسي المسموح به.", "عمادة القبول والتسجيل"),
    (2, "Add/Drop", "Adding or dropping a course during the first week of the semester.", "student", "Academic Advisor",
        "الحذف والإضافة", "إضافة أو حذف مقرر دراسي خلال الأسبوع الأول من الفصل الدراسي.", "المرشد الأكاديمي"),
    (3, "Course Withdrawal", "Withdrawing from a registered course before the withdrawal deadline.", "student", "Admissions and Registration Deanship",
        "الانسحاب من مقرر دراسي", "الانسحاب من مقرر مسجَّل قبل الموعد النهائي للانسحاب.", "عمادة القبول والتسجيل"),
    (4, "Attendance and Absence", "Rules governing lecture attendance and the consequences of excessive absence.", "student", "Academic Department",
        "الحضور والغياب", "قواعد حضور المحاضرات ونتائج الغياب الزائد عن الحد المسموح.", "القسم الأكاديمي"),
    (5, "Study Deferral", "Temporarily postponing enrollment for up to two semesters.", "student", "Academic Department and Admissions and Registration Center",
        "تأجيل الدراسة", "تأجيل الدراسة مؤقتًا لمدة لا تتجاوز فصلين دراسيين.", "القسم الأكاديمي ومركز القبول والتسجيل"),
    (6, "Academic Probation", "Rules and remedial requirements for students below the minimum GPA.", "student", "Academic Advisor",
        "الملاحظة الأكاديمية", "القواعد والمتطلبات العلاجية للطلبة الذين يقل معدلهم عن الحد الأدنى.", "المرشد الأكاديمي"),
    (7, "On-the-Job Training", "The mandatory training course required for graduation.", "student", "Academic Department",
        "التدريب على رأس العمل", "مقرر التدريب الإلزامي المطلوب للتخرج.", "القسم الأكاديمي"),
    (8, "Graduation Requirements", "The requirements a student must meet to be awarded their qualification.", "student", "Admissions and Registration Deanship",
        "متطلبات التخرج", "المتطلبات الواجب على الطالب استيفاؤها لمنحه المؤهل العلمي.", "عمادة القبول والتسجيل"),
    (9, "Course Repeat for Grade Improvement", "Retaking a passed course to improve the overall GPA.", "student", "College Dean",
        "إعادة مقرر لتحسين المعدل", "إعادة دراسة مقرر سبق للطالب النجاح فيه بهدف تحسين المعدل التراكمي.", "عميد الكلية"),
    (10, "Final Grade Appeal", "Requesting a review of a final grade in a specific course.", "student", "Admissions and Registration Center",
        "التظلم من التقدير النهائي", "طلب مراجعة التقدير النهائي لمقرر دراسي معيّن.", "مركز القبول والتسجيل"),
    (11, "Final Exam Absence", "Procedure when a student misses a scheduled final exam.", "student", "Admissions and Registration Center",
        "الغياب عن الاختبار النهائي", "الإجراء المتبع عند تغيّب الطالب عن اختبار نهائي مقرر.", "مركز القبول والتسجيل"),
    (12, "Transfer Between Branches or Programs", "Moving to a different university branch, program, or specialization.", "student", "Admissions and Registration Deanship",
        "الانتقال بين فروع الجامعة أو البرامج", "الانتقال إلى فرع آخر من فروع الجامعة أو برنامج أو تخصص أكاديمي مختلف.", "عمادة القبول والتسجيل"),
    (13, "Re-enrollment After Withdrawal", "Rejoining the university after an official or involuntary withdrawal.", "student", "Academic Department and Admissions and Registration Center",
        "إعادة القيد بعد الانسحاب", "العودة إلى الجامعة بعد الانسحاب الرسمي أو غير الرسمي منها.", "القسم الأكاديمي ومركز القبول والتسجيل"),
    (14, "Maximum Study Duration", "The maximum allowed time to complete each academic level.", "student", "Admissions and Registration Deanship",
        "الحد الأقصى لمدة الدراسة", "الحد الأقصى المسموح به من الزمن لإنهاء كل مستوى دراسي.", "عمادة القبول والتسجيل"),
]

# process_id, step_number, title, description, required_documents, title_ar, description_ar
PROCESS_STEPS = [
    (1, 1, "Check announced registration dates", "The Admissions and Registration Deanship announces registration and add/drop dates before the registration period begins (Art. 19).", None,
        "تحققي من مواعيد التسجيل المعلنة", "تعلن عمادة القبول والتسجيل عن مواعيد التسجيل والحذف والإضافة قبل بدء فترة التسجيل بوقت كافٍ (المادة 19)."),
    (1, 2, "Register within your credit-hour load", "Maximum load is 18 credit hours per Fall/Spring semester; minimum is 12 (full-time) or 6 (part-time), with defined exceptions (Art. 24).", None,
        "سجّلي ضمن العبء الدراسي المسموح", "الحد الأعلى 18 ساعة معتمدة لكل من فصلي الخريف والربيع؛ والحد الأدنى 12 ساعة (تفرغ كامل) أو 6 (تفرغ جزئي)، مع استثناءات محددة (المادة 24)."),
    (1, 3, "Request an overload if eligible", "Up to 21 credit hours is allowed if you meet the GPA conditions in Article 25 (e.g. a 3.50+ semester GPA in two consecutive prior semesters, or being in your graduation semester).", None,
        "اطلبي زيادة العبء الدراسي إن استوفيتِ الشروط", "يجوز تسجيل حتى 21 ساعة معتمدة إذا تحققت شروط المعدل في المادة 25 (مثل معدل فصلي 3.50 فأكثر في فصلين متتاليين، أو كون الطالب في فصل التخرج)."),

    (2, 1, "Add or drop within week 1", "Adding or dropping a course is only allowed during the first week of the semester (Art. 30).", None,
        "الحذف أو الإضافة خلال الأسبوع الأول", "لا يجوز حذف أو إضافة أي مقرر دراسي إلا خلال الأسبوع الأول من بدء الدراسة في الفصل الدراسي (المادة 30)."),
    (2, 2, "Get advisor approval and confirm a seat", "Requires academic advisor approval and an available seat in the course you want to add (Art. 30).", None,
        "احصلي على موافقة المرشد الأكاديمي وتأكدي من توفر مقعد", "يشترط الحصول على موافقة المرشد الأكاديمي، وتوفر مقعد شاغر في المقرر الذي ترغبين بإضافته (المادة 30)."),

    (3, 1, "Withdraw by the deadline", "Withdrawal from a course is allowed up to the end of week 8 of the Fall or Spring semester (Art. 38).", None,
        "انسحبي قبل الموعد النهائي", "يجوز الانسحاب من مقرر دراسي حتى نهاية الأسبوع الثامن من بداية فصلي الخريف أو الربيع (المادة 38)."),
    (3, 2, "Get instructor and advisor approval", "Requires approval from both the course instructor and the academic advisor (Art. 38).", None,
        "احصلي على موافقة مدرّس المقرر والمرشد الأكاديمي", "يشترط الحصول على موافقة مدرّس المقرر الدراسي والمرشد الأكاديمي معًا (المادة 38)."),
    (3, 3, "Stay within the withdrawal limit", "Maximum 2 courses (Diploma level), 1 (Advanced Diploma), 1 (Bachelor level) — or 4 total for Bachelor-only programs — over your entire period of study (Art. 38.1-38.2).", None,
        "لا تتجاوزي الحد المسموح للانسحابات", "الحد الأقصى مقرران في مستوى الدبلوم، ومقرر واحد في الدبلوم المتقدم، ومقرر واحد في البكالوريوس — أو 4 مقررات إجمالًا للبرامج المطروحة على مستوى البكالوريوس فقط — خلال كامل فترة الدراسة (المادة 38 البند 1-2)."),
    (3, 4, "Keep your remaining load above the minimum", "Remaining registered hours after withdrawal must not fall below 12 (full-time), 9 (on academic probation), or 6 (part-time) (Art. 38.3).", None,
        "حافظي على الحد الأدنى للساعات المتبقية", "يجب ألا يقل عدد الساعات المسجلة بعد الانسحاب عن 12 ساعة (تفرغ كامل)، أو 9 (تحت الملاحظة الأكاديمية)، أو 6 (تفرغ جزئي) (المادة 38 البند 3)."),

    (5, 1, "Attend an advising session first", "A mandatory advising session with your academic advisor is required before submitting a deferral request (Art. 40).", None,
        "احضري جلسة إرشاد أولًا", "يخضع الطالب لجلسة توجيه وإرشاد من المرشد الأكاديمي قبل تقديم طلب تأجيل الدراسة (المادة 40)."),
    (5, 2, "Submit by the deadline", "Requests must be submitted no later than week 10 of the semester; a decision is due by the end of week 12 (Art. 40).", None,
        "قدّمي الطلب قبل الموعد النهائي", "يُقدَّم الطلب في موعد أقصاه الأسبوع العاشر من الفصل الدراسي، ويجب البت فيه قبل نهاية الأسبوع الثاني عشر (المادة 40)."),
    (5, 3, "Stay within the maximum deferral period", "Maximum 2 semesters (connected or separate) during your whole period of study; a 3rd exceptional semester is possible with department head recommendation and council approval (Art. 39).", None,
        "لا تتجاوزي الحد الأقصى لفترة التأجيل", "الحد الأقصى فصلان دراسيان (متصلان أو منفصلان) خلال كامل فترة الدراسة، مع إمكانية فصل ثالث استثنائي بتوصية من رئيس القسم وموافقة المجلس (المادة 39)."),

    (6, 1, "Registration is capped while on probation", "No more than 12 and no less than 9 credit hours (full-time), or 6-12 (part-time) (Art. 46).", None,
        "التسجيل محدود أثناء الملاحظة الأكاديمية", "لا يزيد التسجيل عن 12 ساعة معتمدة ولا يقل عن 9 (تفرغ كامل)، أو بين 6 و12 (تفرغ جزئي) (المادة 46)."),
    (6, 2, "Follow your remedial plan", "Your academic advisor sets a remedial plan prioritizing courses you failed or scored below C in (Art. 46).", None,
        "التزمي بالخطة العلاجية", "يضع المرشد الأكاديمي خطة علاجية تمنح الأولوية للمقررات التي رسب فيها الطالب أو حصل فيها على أقل من تقدير (C) (المادة 46)."),
    (6, 3, "Raise your LCGPA within 3 semesters", "You must raise your level cumulative GPA (LCGPA) to 2.00+ within a maximum of 3 consecutive semesters, or you will be mandatorily withdrawn (Art. 47).", None,
        "ارفعي معدلك خلال 3 فصول", "يجب رفع المعدل التراكمي للمستوى الدراسي (LCGPA) إلى 2.00 فأكثر خلال مدة أقصاها 3 فصول دراسية متتالية، وإلا اعتُبر الطالب منسحبًا انسحابًا إلزاميًا (المادة 47)."),

    (7, 1, "Training is a mandatory graded course", "Training/OJT is mandatory for graduation and appears as a coded course on your transcript (Art. 87).", None,
        "التدريب مقرر إلزامي بدرجات", "يُعد التدريب مقررًا إلزاميًا وأساسيًا من متطلبات التخرج، ويُدرج برمز دراسي في كشف درجات الطالب (المادة 87)."),
    (7, 2, "Duration is 8-12 weeks", "Duration ranges from 8 to 12 weeks per the approved course description, and may extend further depending on program requirements (Art. 87).", None,
        "المدة بين 8 و12 أسبوعًا", "تتراوح مدة التدريب بين 8 و12 أسبوعًا حسب توصيف المقرر المعتمد، وقد تطول حسب متطلبات البرنامج الأكاديمي (المادة 87)."),
    (7, 3, "Training time doesn't count against your study limit", "When a training agreement exists with the host institution, the training period is excluded from your maximum study duration and deferral periods (Art. 41).", None,
        "مدة التدريب لا تُحتسب ضمن الحد الأقصى للدراسة", "في حال وجود اتفاقية تدريب مع الجهة المضيفة، لا تُحتسب مدة التدريب ضمن الحد الأقصى للدراسة أو فترات التأجيل (المادة 41)."),

    (8, 1, "Complete your study plan", "Successfully complete all courses required by your program's graduation plan (Art. 88).", None,
        "أكملي خطتك الدراسية", "إكمال متطلبات الخطة الدراسية للبرنامج بنجاح (المادة 88)."),
    (8, 2, "Pass the training course", "Successful completion of the mandatory training/OJT course is required (Art. 87, 88).", None,
        "اجتازي مقرر التدريب", "يشترط إكمال مقرر التدريب الإلزامي بنجاح (المادتان 87 و88)."),
    (8, 3, "Meet the minimum CGPA", "An overall cumulative GPA (CGPA) of 2.00 or higher is required to graduate (Art. 88).", None,
        "استوفي الحد الأدنى للمعدل التراكمي الكلي", "يشترط الحصول على معدل تراكمي كلي (CGPA) لا يقل عن 2.00 للتخرج (المادة 88)."),

    (9, 1, "Check your eligibility", "You may repeat a course you passed with a C or lower to improve your grade, subject to seat availability (Art. 33).", None,
        "تحققي من استيفاء الشروط", "يجوز إعادة مقرر نجح فيه الطالب بتقدير (C) فأقل لتحسين المعدل، وذلك حسب توفر المقاعد الشاغرة (المادة 33)."),
    (9, 2, "Stay within the repeat limit", "Up to 2 courses (Diploma), 1 (Advanced Diploma), 1 (Bachelor) — or 4 total for Bachelor-only programs (Art. 33).", None,
        "لا تتجاوزي الحد المسموح للإعادة", "بحد أقصى مقررين في الدبلوم، ومقرر واحد في الدبلوم المتقدم، ومقرر واحد في البكالوريوس — أو 4 مقررات إجمالًا للبرامج المطروحة على مستوى البكالوريوس فقط (المادة 33)."),

    (10, 1, "Submit within 3 working days", "Grade-review requests must be submitted within 3 working days of the final result announcement (Art. 77).", None,
        "قدّمي الطلب خلال 3 أيام عمل", "يُقدَّم طلب مراجعة التقدير خلال مدة أقصاها 3 أيام عمل من تاريخ إعلان النتيجة النهائية (المادة 77)."),
    (10, 2, "First appeal is free", "Your first course appeal has no fee; fees for additional courses are refunded if an error is found (Art. 77).", None,
        "التظلم الأول بدون رسوم", "يحق للطالب التظلم في مقرر واحد بدون رسوم، وتُستَرد رسوم المقررات الأخرى في حال وجود خطأ في التقدير (المادة 77)."),
    (10, 3, "Decision timeline", "The department must decide within the end of week 1 of the following semester; no response counts as rejection (Art. 78).", None,
        "الجدول الزمني للبت بالطلب", "يجب البت في التظلم خلال مدة لا تتجاوز نهاية الأسبوع الأول من الفصل الدراسي التالي، ويُعد عدم الرد بمثابة رفض (المادة 78)."),

    (11, 1, "You receive an Incomplete (IC) grade", "Missing a final exam results in an 'Incomplete (IC)' grade pending your excuse (Art. 72).", None,
        "يُمنح تقدير غير مكتمل (IC)", "يترتب على التغيب عن الاختبار النهائي منح تقدير (غير مكتمل) (ك) لحين تقديم العذر والبت فيه (المادة 72)."),
    (11, 2, "Submit your excuse within 3 working days", "The excuse must reach the Admissions and Registration Center within 3 working days of the exam date (Art. 72).", None,
        "قدّمي العذر خلال 3 أيام عمل", "يجب تقديم عذر الغياب إلى مركز القبول والتسجيل خلال مدة أقصاها 3 أيام عمل من تاريخ عقد الاختبار (المادة 72)."),
    (11, 3, "Makeup exam scheduling", "Makeup exams for accepted excuses are held within week 1 of the following semester (Art. 74).", None,
        "موعد الاختبار التكميلي", "تُعقد الاختبارات التكميلية للأعذار المقبولة خلال الأسبوع الأول من بداية الفصل الدراسي التالي (المادة 74)."),
    (11, 4, "Unaccepted excuse consequence", "If the excuse is not accepted, you receive a zero on that exam and your final grade is calculated from your semester work only (Art. 72).", None,
        "نتيجة عدم قبول العذر", "في حال عدم قبول العذر، يُرصد للطالب (صفر) في ذلك الاختبار، ويُحسب التقدير النهائي وفق مجموع أعمال الفصل فقط (المادة 72)."),

    (12, 1, "Minimum timing", "Transfer requests between branches/programs may be submitted starting week 6 of any semester, except the summer semester (Art. 14).", None,
        "التوقيت المسموح", "يجوز تقديم طلبات الانتقال بدءًا من الأسبوع السادس من أي فصل دراسي باستثناء الفصل الصيفي (المادة 14)."),
    (12, 2, "Program/major change limit", "You may change your academic program or specialization only once during your entire period of study (Art. 14).", None,
        "حد تغيير البرنامج أو التخصص", "يحق للطالب تغيير البرنامج الأكاديمي أو التخصص مرة واحدة فقط خلال فترة الدراسة بالجامعة (المادة 14)."),
    (12, 3, "Additional condition for major changes", "Changing major additionally requires that you have not completed more than one academic year in your current program (Art. 14.2.d).", None,
        "شرط إضافي لتغيير التخصص", "يشترط لتغيير التخصص ألا يكون الطالب قد أكمل أكثر من عام أكاديمي واحد في برنامجه أو تخصصه الحالي (المادة 14 البند 2-د)."),

    (13, 1, "Break period limit", "The gap since withdrawal must not exceed 2 semesters, extendable by Academic Council approval with supporting reports (Art. 45.1).", None,
        "الحد الأقصى لفترة الانقطاع", "ألا تزيد فترة الانقطاع عن فصلين دراسيين، مع إمكانية مدها بموافقة المجلس الأكاديمي وتقارير مؤيدة (المادة 45 البند 1)."),
    (13, 2, "Justify the withdrawal", "You must provide evidence that your prior withdrawal had an acceptable excuse (Art. 45.2).", None,
        "تبرير الانسحاب السابق", "يجب تقديم ما يثبت أن الانقطاع السابق كان بعذر مقبول (المادة 45 البند 2)."),
    (13, 3, "Seat availability", "Requires an available seat in your branch/program; priority goes to students who completed more credit hours if seats are limited (Art. 45.3).", None,
        "توفر مقعد شاغر", "يشترط توفر مقعد شاغر في الفرع أو البرنامج، مع إعطاء الأولوية لمن أنجز عددًا أكبر من الساعات المعتمدة عند محدودية المقاعد (المادة 45 البند 3)."),

    (14, 1, "Diploma", "Maximum 3 years full-time (6 years part-time) after completing the Foundation Program (Art. 57.1).", None,
        "الدبلوم", "الحد الأقصى 3 سنوات دراسية (تفرغ كامل) أو 6 سنوات (تفرغ جزئي) بعد إنهاء البرنامج التأسيسي بنجاح (المادة 57 البند 1)."),
    (14, 2, "Advanced Diploma", "Maximum 2 years full-time (4 years part-time) after completing all Diploma-level requirements (Art. 57.2).", None,
        "الدبلوم المتقدم", "الحد الأقصى سنتان دراسيتان (تفرغ كامل) أو 4 سنوات (تفرغ جزئي) بعد إنهاء جميع متطلبات مستوى الدبلوم (المادة 57 البند 2)."),
    (14, 3, "Bachelor's degree", "Maximum 2 years full-time (4 years part-time) after completing all Advanced Diploma requirements; Bachelor-only programs allow up to 6 years total after the Foundation Program (Art. 57.3).", None,
        "البكالوريوس", "الحد الأقصى سنتان دراسيتان (تفرغ كامل) أو 4 سنوات (تفرغ جزئي) بعد إنهاء متطلبات الدبلوم المتقدم؛ وتصل إلى 6 سنوات إجمالًا بعد البرنامج التأسيسي للبرامج المطروحة على مستوى البكالوريوس فقط (المادة 57 البند 3)."),
]

# process_id, question, answer, question_ar, answer_ar
FAQS = [
    (1, "What is the maximum credit-hour load per semester?",
        "18 credit hours is the maximum course load for a Fall or Spring semester (Article 24).",
        "كم أقصى عدد ساعات معتمدة أقدر أسجّلها في الفصل؟",
        "18 ساعة معتمدة هو الحد الأقصى للعبء الدراسي في فصل الخريف أو الربيع (المادة 24)."),
    (1, "What is the minimum credit-hour load per semester?",
        "12 credit hours is the minimum for full-time students in Fall/Spring; part-time students may register as few as 6, with other defined exceptions (Article 24).",
        "كم أقل عدد ساعات معتمدة لازم أسجّلها في الفصل؟",
        "12 ساعة معتمدة هو الحد الأدنى للطلبة بنظام التفرغ الكامل في الخريف والربيع؛ ويجوز لطلبة التفرغ الجزئي تسجيل 6 ساعات كحد أدنى، مع استثناءات أخرى محددة (المادة 24)."),
    (1, "Can I register for more than 18 credit hours?",
        "Yes, up to 21 credit hours, if you achieved at least a 3.50 semester GPA over 15+ hours in two consecutive semesters, or a 3.50+ level GPA (LCGPA), or if you are in your graduation semester (Article 25).",
        "هل أقدر أسجّل أكثر من 18 ساعة معتمدة؟",
        "نعم، حتى 21 ساعة معتمدة، إذا حققتِ معدلًا فصليًا 3.50 فأكثر بعبء 15 ساعة فأكثر في فصلين متتاليين، أو معدلًا تراكميًا للمستوى (LCGPA) 3.50 فأكثر، أو إذا كنتِ في فصل التخرج (المادة 25)."),
    (1, "How many students are needed for a course to run?",
        "At least 10 students must register for a course to be offered in the Fall or Spring semester, unless the Branch/College Council grants an exception (Article 19).",
        "كم عدد الطلبة المطلوب لطرح مقرر دراسي؟",
        "يشترط تسجيل 10 طلبة على الأقل لطرح المقرر في فصلي الخريف أو الربيع، إلا إذا استثنى مجلس الفرع أو الكلية من ذلك (المادة 19)."),

    (3, "Until when can I withdraw from a course?",
        "You can withdraw from a course up to the end of week 8 of the Fall or Spring semester, with instructor and academic advisor approval (Article 38).",
        "إلى متى أقدر أنسحب من مقرر دراسي؟",
        "يجوز الانسحاب من مقرر حتى نهاية الأسبوع الثامن من فصل الخريف أو الربيع، بموافقة مدرّس المقرر والمرشد الأكاديمي (المادة 38)."),
    (3, "How many courses can I withdraw from during my studies?",
        "Up to 2 courses at Diploma level, 1 at Advanced Diploma level, and 1 at Bachelor level — or up to 4 total for Bachelor-only programs (Article 38).",
        "كم مقرر أقدر أنسحب منه خلال فترة دراستي؟",
        "حتى مقررين في مستوى الدبلوم، ومقرر واحد في الدبلوم المتقدم، ومقرر واحد في البكالوريوس — أو حتى 4 مقررات إجمالًا للبرامج المطروحة على مستوى البكالوريوس فقط (المادة 38)."),
    (3, "What is the minimum credit load I must keep after withdrawing?",
        "After withdrawal, your registered load must not fall below 12 credit hours (full-time), 9 (if on academic probation), or 6 (part-time) (Article 38.3).",
        "كم أقل عدد ساعات لازم يضل مسجّل بعد الانسحاب؟",
        "بعد الانسحاب، يجب ألا يقل عدد الساعات المسجلة عن 12 ساعة (تفرغ كامل)، أو 9 (تحت الملاحظة الأكاديمية)، أو 6 (تفرغ جزئي) (المادة 38 البند 3)."),

    (4, "What happens if I miss more than 20% of a course's teaching hours?",
        "With an accepted excuse, you are withdrawn from the course (grade W). Without an accepted excuse, you fail the course with a 'Fail due to Absence' (FW) grade (Article 59).",
        "وش يصير لو غبت أكثر من 20% من ساعات المقرر؟",
        "مع عذر مقبول، يُعد الطالب منسحبًا من المقرر بتقدير (منسحب) (W). وبدون عذر مقبول، يُمنح تقدير (راسب بسبب الغياب) (FW) (المادة 59)."),
    (4, "How many absence warnings do I get before being barred from the final exam?",
        "A first warning at 10% absence, a second warning at 15%, and being barred from the final exam (counted as a fail) at over 20% absence in a course (Article 58).",
        "كم إنذار غياب أحصل قبل ما أُحرم من الاختبار النهائي؟",
        "إنذار أول عند نسبة غياب 10%، وإنذار ثانٍ عند 15%، والحرمان من دخول الاختبار النهائي (واعتباره راسبًا) عند تجاوز الغياب 20% في المقرر (المادة 58)."),

    (5, "How long can I defer my studies?",
        "A maximum of 2 semesters total (connected or separate) during your entire period of study; a 3rd exceptional semester is possible with department head recommendation and council approval (Article 39).",
        "كم مدة أقدر أأجّل فيها دراستي؟",
        "الحد الأقصى فصلان دراسيان إجمالًا (متصلان أو منفصلان) خلال كامل فترة الدراسة؛ مع إمكانية فصل ثالث استثنائي بتوصية من رئيس القسم وموافقة المجلس (المادة 39)."),
    (5, "Will I receive my stipend during a deferral period?",
        "No — subsistence allowances are not paid during a deferral period, in any case (Article 39).",
        "هل بستمر أستلم مخصصات الإعاشة أثناء فترة التأجيل؟",
        "لا — لا تُصرف مخصصات الإعاشة خلال فترة التأجيل بأي حال من الأحوال (المادة 39)."),
    (5, "When is the deadline to request a study deferral?",
        "No later than week 10 of the semester; the university must decide on the request by the end of week 12 (Article 40).",
        "متى آخر موعد لتقديم طلب تأجيل الدراسة؟",
        "في موعد أقصاه الأسبوع العاشر من الفصل الدراسي، ويجب أن تبت الجامعة في الطلب قبل نهاية الأسبوع الثاني عشر (المادة 40)."),

    (6, "What GPA puts me on academic probation?",
        "A semester GPA or level cumulative GPA (LCGPA) below 2.00 places you on academic probation the following semester (Article 46).",
        "أي معدل يخليني تحت الملاحظة الأكاديمية؟",
        "المعدل الفصلي أو المعدل التراكمي للمستوى (LCGPA) الأقل من 2.00 يضع الطالب تحت الملاحظة الأكاديمية في الفصل التالي (المادة 46)."),
    (6, "How long do I have to get off academic probation?",
        "You must raise your LCGPA to 2.00 or above within a maximum of 3 consecutive semesters, or you will be mandatorily withdrawn from the university (Article 47).",
        "كم مهلتي عشان أطلع من الملاحظة الأكاديمية؟",
        "يجب رفع المعدل التراكمي للمستوى (LCGPA) إلى 2.00 فأكثر خلال مدة أقصاها 3 فصول دراسية متتالية، وإلا يُعد الطالب منسحبًا انسحابًا إلزاميًا من الجامعة (المادة 47)."),
    (6, "How many credit hours can I register while on academic probation?",
        "No more than 12 and no less than 9 credit hours for full-time students, or between 6 and 12 for part-time students (Article 46).",
        "كم ساعة معتمدة أقدر أسجّل وأنا تحت الملاحظة الأكاديمية؟",
        "لا يزيد التسجيل عن 12 ساعة معتمدة ولا يقل عن 9 لطلبة التفرغ الكامل، أو بين 6 و12 لطلبة التفرغ الجزئي (المادة 46)."),

    (7, "How long is the mandatory training/OJT course?",
        "Between 8 and 12 weeks, according to the approved course description, and it may extend further depending on program requirements (Article 87).",
        "كم مدة مقرر التدريب الإلزامي؟",
        "بين 8 و12 أسبوعًا حسب توصيف المقرر المعتمد، وقد تطول المدة حسب متطلبات البرنامج الأكاديمي (المادة 87)."),
    (7, "Does the training period count toward my maximum study duration?",
        "No — when there is a training agreement with the host institution, the training period is excluded from both your maximum study duration and any deferral periods (Article 41).",
        "هل مدة التدريب تُحتسب ضمن الحد الأقصى لمدة دراستي؟",
        "لا — عند وجود اتفاقية تدريب مع الجهة المضيفة، لا تُحتسب مدة التدريب ضمن الحد الأقصى للدراسة ولا ضمن فترات التأجيل (المادة 41)."),

    (8, "What GPA do I need to graduate?",
        "An overall cumulative GPA (CGPA) of 2.00 or higher, along with successful completion of all study-plan requirements and the training course (Article 88).",
        "أي معدل أحتاجه عشان أتخرج؟",
        "معدل تراكمي كلي (CGPA) لا يقل عن 2.00، مع إكمال جميع متطلبات الخطة الدراسية ومقرر التدريب بنجاح (المادة 88)."),

    (9, "Can I retake a course I already passed to improve my grade?",
        "Yes, if you passed it with a C or lower — up to 2 courses at Diploma level, 1 at Advanced Diploma, 1 at Bachelor level (or 4 total for Bachelor-only programs), subject to seat availability (Article 33).",
        "هل أقدر أعيد مقرر سبق نجاحي فيه لتحسين المعدل؟",
        "نعم، إذا نجحتِ فيه بتقدير (C) فأقل — حتى مقررين في الدبلوم، ومقرر واحد في الدبلوم المتقدم، ومقرر واحد في البكالوريوس (أو 4 مقررات إجمالًا للبرامج المطروحة على مستوى البكالوريوس فقط)، حسب توفر المقاعد (المادة 33)."),
    (9, "Do repeated courses count in my GPA?",
        "Yes. All attempts appear on your transcript, and the second and later attempts count toward your GPA even if the grade is lower than a previous attempt (Article 34).",
        "هل المقررات المعادة تدخل في حساب معدلي؟",
        "نعم. تظهر جميع المحاولات في كشف الدرجات، وتُحتسب المحاولة الثانية وما بعدها في المعدل حتى لو كان التقدير أقل من المحاولة السابقة (المادة 34)."),

    (10, "How long do I have to appeal a final grade?",
        "3 working days from the announcement of the final result; your first course appeal in that period is free of charge (Article 77).",
        "كم مهلتي للتظلم من تقدير نهائي؟",
        "3 أيام عمل من تاريخ إعلان النتيجة النهائية؛ والتظلم الأول خلال هذه المدة بدون رسوم (المادة 77)."),

    (11, "What happens if I miss the final exam with an accepted excuse?",
        "You receive an 'Incomplete (IC)' grade, and a makeup exam is scheduled within week 1 of the following semester (Articles 72 and 74).",
        "وش يصير لو غبت عن الاختبار النهائي بعذر مقبول؟",
        "يُمنح الطالب تقدير (غير مكتمل) (ك)، ويُحدَّد له اختبار تكميلي خلال الأسبوع الأول من الفصل الدراسي التالي (المادتان 72 و74)."),
    (11, "What if my excuse for missing the final exam is not accepted?",
        "You receive a zero on that exam, and your final grade is calculated from your semester coursework only (Article 72).",
        "وش يصير لو عذري عن الاختبار النهائي ما انقبل؟",
        "يُرصد للطالب (صفر) في ذلك الاختبار، ويُحسب التقدير النهائي وفق مجموع أعمال الفصل فقط (المادة 72)."),

    (12, "Can I transfer to another branch or program?",
        "Yes, starting week 6 of any semester except summer, subject to conditions including seat availability (Article 14).",
        "هل أقدر أنتقل لفرع أو برنامج آخر؟",
        "نعم، بدءًا من الأسبوع السادس من أي فصل دراسي عدا الصيفي، وفق شروط منها توفر مقعد شاغر (المادة 14)."),
    (12, "How many times can I change my academic program or specialization?",
        "Only once during your entire period of study at the university (Article 14).",
        "كم مرة أقدر أغيّر فيها برنامجي أو تخصصي الأكاديمي؟",
        "مرة واحدة فقط خلال كامل فترة الدراسة بالجامعة (المادة 14)."),

    (13, "Can I re-enroll after withdrawing from the university?",
        "Yes, once only, subject to conditions including a break not exceeding 2 semesters and an available seat, with priority given to students who completed more credit hours (Article 45).",
        "هل أقدر أرجع للجامعة بعد الانسحاب؟",
        "نعم، مرة واحدة فقط، وفق شروط منها ألا تتجاوز فترة الانقطاع فصلين دراسيين وتوفر مقعد شاغر، مع إعطاء الأولوية لمن أنجز ساعات معتمدة أكثر (المادة 45)."),

    (14, "What is the maximum time allowed to complete a diploma?",
        "3 years full-time (6 years part-time) after completing the Foundation Program (Article 57.1).",
        "كم الحد الأقصى لإنهاء الدبلوم؟",
        "3 سنوات دراسية بنظام التفرغ الكامل (6 سنوات بالتفرغ الجزئي) بعد إنهاء البرنامج التأسيسي بنجاح (المادة 57 البند 1)."),
    (14, "What is the maximum time allowed to complete a bachelor's degree?",
        "2 years full-time (4 years part-time) after completing all Advanced Diploma requirements, or up to 6 years total after the Foundation Program for Bachelor-only programs (Article 57.3).",
        "كم الحد الأقصى لإنهاء درجة البكالوريوس؟",
        "سنتان دراسيتان بنظام التفرغ الكامل (4 سنوات بالتفرغ الجزئي) بعد إنهاء متطلبات الدبلوم المتقدم، أو حتى 6 سنوات إجمالًا بعد البرنامج التأسيسي للبرامج المطروحة على مستوى البكالوريوس فقط (المادة 57 البند 3)."),
]


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    conn.executemany(
        "INSERT INTO processes (id, name, description, applies_to_role, responsible_office, name_ar, description_ar, responsible_office_ar) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        PROCESSES,
    )
    conn.executemany(
        "INSERT INTO process_steps (process_id, step_number, title, description, required_documents, title_ar, description_ar) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        PROCESS_STEPS,
    )
    conn.executemany(
        "INSERT INTO faqs (process_id, question, answer, last_verified_date, verified_by, question_ar, answer_ar, verified_by_ar) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(pid, q, a, VERIFIED_DATE, SOURCE_EN, q_ar, a_ar, SOURCE_AR) for (pid, q, a, q_ar, a_ar) in FAQS],
    )
    conn.executemany(
        "INSERT INTO stakeholders (role, department, program) VALUES (?, ?, ?)",
        [("student", "IT", "Software Engineering"), ("advisor", "IT", None), ("staff", "Registrar", None)],
    )

    conn.commit()
    conn.close()
    print(f"Database built at {DB_PATH} — {len(PROCESSES)} processes, {len(FAQS)} FAQs (bilingual EN/AR), sourced from {SOURCE_EN}.")


if __name__ == "__main__":
    build()
