"""
Builds institutional_processes.db from the real, published UTAS Academic
Regulation (Decision No. 612/2022, Official Gazette No. 1468, effective
2022/2023 academic year onward). Every process, step and FAQ below is
sourced from a specific article of that regulation — this replaces the
earlier placeholder/sample dataset entirely.

Coverage note: this is a curated set of the most commonly-asked
regulations (registration, withdrawal, probation, deferral, training,
graduation, repeats, appeals, exam absence, transfer, re-enrollment,
maximum study duration) — not a verbatim reproduction of all 92 articles.
A Q&A agent works from discrete question/answer pairs matching what
students actually ask, not a full legal-text dump. Extend this file with
more FAQs (same structure) for any additional article-based questions
that come up in practice.

Responsible-office labels use the roles named in the regulation itself
(e.g. "Admissions and Registration Deanship", "Academic Advisor") rather
than any specific person, matching Article 12's data-privacy provision.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "institutional_processes.db")
SOURCE = "UTAS Academic Regulation (Decision 612/2022)"
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
    responsible_office TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS process_steps (
    id INTEGER PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id),
    step_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    required_documents TEXT
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
    verified_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    question TEXT NOT NULL,
    matched_process_ids TEXT,
    matched_faq_ids TEXT,
    qa_passed INTEGER NOT NULL,
    qa_notes TEXT
);
"""

PROCESSES = [
    # id, name, description, applies_to_role, responsible_office
    (1, "Course Registration and Load", "Registering for courses each semester within the allowed credit-hour load.", "student", "Admissions and Registration Deanship"),
    (2, "Add/Drop", "Adding or dropping a course during the first week of the semester.", "student", "Academic Advisor"),
    (3, "Course Withdrawal", "Withdrawing from a registered course before the withdrawal deadline.", "student", "Admissions and Registration Deanship"),
    (4, "Attendance and Absence", "Rules governing lecture attendance and the consequences of excessive absence.", "student", "Academic Department"),
    (5, "Study Deferral", "Temporarily postponing enrollment for up to two semesters.", "student", "Academic Department and Admissions and Registration Center"),
    (6, "Academic Probation", "Rules and remedial requirements for students below the minimum GPA.", "student", "Academic Advisor"),
    (7, "On-the-Job Training", "The mandatory training course required for graduation.", "student", "Academic Department"),
    (8, "Graduation Requirements", "The requirements a student must meet to be awarded their qualification.", "student", "Admissions and Registration Deanship"),
    (9, "Course Repeat for Grade Improvement", "Retaking a passed course to improve the overall GPA.", "student", "College Dean"),
    (10, "Final Grade Appeal", "Requesting a review of a final grade in a specific course.", "student", "Admissions and Registration Center"),
    (11, "Final Exam Absence", "Procedure when a student misses a scheduled final exam.", "student", "Admissions and Registration Center"),
    (12, "Transfer Between Branches or Programs", "Moving to a different university branch, program, or specialization.", "student", "Admissions and Registration Deanship"),
    (13, "Re-enrollment After Withdrawal", "Rejoining the university after an official or involuntary withdrawal.", "student", "Academic Department and Admissions and Registration Center"),
    (14, "Maximum Study Duration", "The maximum allowed time to complete each academic level.", "student", "Admissions and Registration Deanship"),
]

PROCESS_STEPS = [
    # process_id, step_number, title, description, required_documents
    (1, 1, "Check announced registration dates", "The Admissions and Registration Deanship announces registration and add/drop dates before the registration period begins (Art. 19).", None),
    (1, 2, "Register within your credit-hour load", "Maximum load is 18 credit hours per Fall/Spring semester; minimum is 12 (full-time) or 6 (part-time), with defined exceptions (Art. 24).", None),
    (1, 3, "Request an overload if eligible", "Up to 21 credit hours is allowed if you meet the GPA conditions in Article 25 (e.g. a 3.50+ semester GPA in two consecutive prior semesters, or being in your graduation semester).", None),

    (2, 1, "Add or drop within week 1", "Adding or dropping a course is only allowed during the first week of the semester (Art. 30).", None),
    (2, 2, "Get advisor approval and confirm a seat", "Requires academic advisor approval and an available seat in the course you want to add (Art. 30).", None),

    (3, 1, "Withdraw by the deadline", "Withdrawal from a course is allowed up to the end of week 8 of the Fall or Spring semester (Art. 38).", None),
    (3, 2, "Get instructor and advisor approval", "Requires approval from both the course instructor and the academic advisor (Art. 38).", None),
    (3, 3, "Stay within the withdrawal limit", "Maximum 2 courses (Diploma level), 1 (Advanced Diploma), 1 (Bachelor level) — or 4 total for Bachelor-only programs — over your entire period of study (Art. 38.1-38.2).", None),
    (3, 4, "Keep your remaining load above the minimum", "Remaining registered hours after withdrawal must not fall below 12 (full-time), 9 (on academic probation), or 6 (part-time) (Art. 38.3).", None),

    (5, 1, "Attend an advising session first", "A mandatory advising session with your academic advisor is required before submitting a deferral request (Art. 40).", None),
    (5, 2, "Submit by the deadline", "Requests must be submitted no later than week 10 of the semester; a decision is due by the end of week 12 (Art. 40).", None),
    (5, 3, "Stay within the maximum deferral period", "Maximum 2 semesters (connected or separate) during your whole period of study; a 3rd exceptional semester is possible with department head recommendation and Branch/College Council approval (Art. 39).", None),

    (6, 1, "Registration is capped while on probation", "No more than 12 and no less than 9 credit hours (full-time), or 6-12 (part-time) (Art. 46).", None),
    (6, 2, "Follow your remedial plan", "Your academic advisor sets a remedial plan prioritizing courses you failed or scored below C in (Art. 46).", None),
    (6, 3, "Raise your LCGPA within 3 semesters", "You must raise your level cumulative GPA (LCGPA) to 2.00+ within a maximum of 3 consecutive semesters, or you will be mandatorily withdrawn (Art. 47).", None),

    (7, 1, "Training is a mandatory graded course", "Training/OJT is mandatory for graduation and appears as a coded course on your transcript (Art. 87).", None),
    (7, 2, "Duration is 8-12 weeks", "Duration ranges from 8 to 12 weeks per the approved course description, and may extend further depending on program requirements (Art. 87).", None),
    (7, 3, "Training time doesn't count against your study limit", "When a training agreement exists with the host institution, the training period is excluded from your maximum study duration and deferral periods (Art. 41).", None),

    (8, 1, "Complete your study plan", "Successfully complete all courses required by your program's graduation plan (Art. 88).", None),
    (8, 2, "Pass the training course", "Successful completion of the mandatory training/OJT course is required (Art. 87, 88).", None),
    (8, 3, "Meet the minimum CGPA", "An overall cumulative GPA (CGPA) of 2.00 or higher is required to graduate (Art. 88).", None),

    (9, 1, "Check your eligibility", "You may repeat a course you passed with a C or lower to improve your grade, subject to seat availability (Art. 33).", None),
    (9, 2, "Stay within the repeat limit", "Up to 2 courses (Diploma), 1 (Advanced Diploma), 1 (Bachelor) — or 4 total for Bachelor-only programs (Art. 33).", None),

    (10, 1, "Submit within 3 working days", "Grade-review requests must be submitted within 3 working days of the final result announcement (Art. 77).", None),
    (10, 2, "First appeal is free", "Your first course appeal has no fee; fees for additional courses are refunded if an error is found (Art. 77).", None),
    (10, 3, "Decision timeline", "The department must decide within the end of week 1 of the following semester; no response counts as rejection (Art. 78).", None),

    (11, 1, "You receive an Incomplete (IC) grade", "Missing a final exam results in an 'Incomplete (IC)' grade pending your excuse (Art. 72).", None),
    (11, 2, "Submit your excuse within 3 working days", "The excuse must reach the Admissions and Registration Center within 3 working days of the exam date (Art. 72).", None),
    (11, 3, "Makeup exam scheduling", "Makeup exams for accepted excuses are held within week 1 of the following semester (Art. 74).", None),
    (11, 4, "Unaccepted excuse consequence", "If the excuse is not accepted, you receive a zero on that exam and your final grade is calculated from your semester work only (Art. 72).", None),

    (12, 1, "Minimum timing", "Transfer requests between branches/programs may be submitted starting week 6 of any semester, except the summer semester (Art. 14).", None),
    (12, 2, "Program/major change limit", "You may change your academic program or specialization only once during your entire period of study (Art. 14).", None),
    (12, 3, "Additional condition for major changes", "Changing major additionally requires that you have not completed more than one academic year in your current program (Art. 14.2.d).", None),

    (13, 1, "Break period limit", "The gap since withdrawal must not exceed 2 semesters, extendable by Academic Council approval with supporting reports (Art. 45.1).", None),
    (13, 2, "Justify the withdrawal", "You must provide evidence that your prior withdrawal had an acceptable excuse (Art. 45.2).", None),
    (13, 3, "Seat availability", "Requires an available seat in your branch/program; priority goes to students who completed more credit hours if seats are limited (Art. 45.3).", None),

    (14, 1, "Diploma", "Maximum 3 years full-time (6 years part-time) after completing the Foundation Program (Art. 57.1).", None),
    (14, 2, "Advanced Diploma", "Maximum 2 years full-time (4 years part-time) after completing all Diploma-level requirements (Art. 57.2).", None),
    (14, 3, "Bachelor's degree", "Maximum 2 years full-time (4 years part-time) after completing all Advanced Diploma requirements; Bachelor-only programs allow up to 6 years total after the Foundation Program (Art. 57.3).", None),
]

FAQS = [
    # process_id, question, answer
    (1, "What is the maximum credit-hour load per semester?",
        "18 credit hours is the maximum course load for a Fall or Spring semester (Article 24)."),
    (1, "What is the minimum credit-hour load per semester?",
        "12 credit hours is the minimum for full-time students in Fall/Spring; part-time students may register as few as 6, with other defined exceptions (Article 24)."),
    (1, "Can I register for more than 18 credit hours?",
        "Yes, up to 21 credit hours, if you achieved at least a 3.50 semester GPA over 15+ hours in two consecutive semesters, or a 3.50+ level GPA (LCGPA), or if you are in your graduation semester (Article 25)."),
    (1, "How many students are needed for a course to run?",
        "At least 10 students must register for a course to be offered in the Fall or Spring semester, unless the Branch/College Council grants an exception (Article 19)."),

    (3, "Until when can I withdraw from a course?",
        "You can withdraw from a course up to the end of week 8 of the Fall or Spring semester, with instructor and academic advisor approval (Article 38)."),
    (3, "How many courses can I withdraw from during my studies?",
        "Up to 2 courses at Diploma level, 1 at Advanced Diploma level, and 1 at Bachelor level — or up to 4 total for Bachelor-only programs (Article 38)."),
    (3, "What is the minimum credit load I must keep after withdrawing?",
        "After withdrawal, your registered load must not fall below 12 credit hours (full-time), 9 (if on academic probation), or 6 (part-time) (Article 38.3)."),

    (4, "What happens if I miss more than 20% of a course's teaching hours?",
        "With an accepted excuse, you are withdrawn from the course (grade W). Without an accepted excuse, you fail the course with a 'Fail due to Absence' (FW) grade (Article 59)."),
    (4, "How many absence warnings do I get before being barred from the final exam?",
        "A first warning at 10% absence, a second warning at 15%, and being barred from the final exam (counted as a fail) at over 20% absence in a course (Article 58)."),

    (5, "How long can I defer my studies?",
        "A maximum of 2 semesters total (connected or separate) during your entire period of study; a 3rd exceptional semester is possible with department head recommendation and council approval (Article 39)."),
    (5, "Will I receive my stipend during a deferral period?",
        "No — subsistence allowances are not paid during a deferral period, in any case (Article 39)."),
    (5, "When is the deadline to request a study deferral?",
        "No later than week 10 of the semester; the university must decide on the request by the end of week 12 (Article 40)."),

    (6, "What GPA puts me on academic probation?",
        "A semester GPA or level cumulative GPA (LCGPA) below 2.00 places you on academic probation the following semester (Article 46)."),
    (6, "How long do I have to get off academic probation?",
        "You must raise your LCGPA to 2.00 or above within a maximum of 3 consecutive semesters, or you will be mandatorily withdrawn from the university (Article 47)."),
    (6, "How many credit hours can I register while on academic probation?",
        "No more than 12 and no less than 9 credit hours for full-time students, or between 6 and 12 for part-time students (Article 46)."),

    (7, "How long is the mandatory training/OJT course?",
        "Between 8 and 12 weeks, according to the approved course description, and it may extend further depending on program requirements (Article 87)."),
    (7, "Does the training period count toward my maximum study duration?",
        "No — when there is a training agreement with the host institution, the training period is excluded from both your maximum study duration and any deferral periods (Article 41)."),

    (8, "What GPA do I need to graduate?",
        "An overall cumulative GPA (CGPA) of 2.00 or higher, along with successful completion of all study-plan requirements and the training course (Article 88)."),

    (9, "Can I retake a course I already passed to improve my grade?",
        "Yes, if you passed it with a C or lower — up to 2 courses at Diploma level, 1 at Advanced Diploma, 1 at Bachelor level (or 4 total for Bachelor-only programs), subject to seat availability (Article 33)."),
    (9, "Do repeated courses count in my GPA?",
        "Yes. All attempts appear on your transcript, and the second and later attempts count toward your GPA even if the grade is lower than a previous attempt (Article 34)."),

    (10, "How long do I have to appeal a final grade?",
        "3 working days from the announcement of the final result; your first course appeal in that period is free of charge (Article 77)."),

    (11, "What happens if I miss the final exam with an accepted excuse?",
        "You receive an 'Incomplete (IC)' grade, and a makeup exam is scheduled within week 1 of the following semester (Articles 72 and 74)."),
    (11, "What if my excuse for missing the final exam is not accepted?",
        "You receive a zero on that exam, and your final grade is calculated from your semester coursework only (Article 72)."),

    (12, "Can I transfer to another branch or program?",
        "Yes, starting week 6 of any semester except summer, subject to conditions including seat availability (Article 14)."),
    (12, "How many times can I change my academic program or specialization?",
        "Only once during your entire period of study at the university (Article 14)."),

    (13, "Can I re-enroll after withdrawing from the university?",
        "Yes, once only, subject to conditions including a break not exceeding 2 semesters and an available seat, with priority given to students who completed more credit hours (Article 45)."),

    (14, "What is the maximum time allowed to complete a diploma?",
        "3 years full-time (6 years part-time) after completing the Foundation Program (Article 57.1)."),
    (14, "What is the maximum time allowed to complete a bachelor's degree?",
        "2 years full-time (4 years part-time) after completing all Advanced Diploma requirements, or up to 6 years total after the Foundation Program for Bachelor-only programs (Article 57.3)."),
]


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    conn.executemany(
        "INSERT INTO processes (id, name, description, applies_to_role, responsible_office) VALUES (?, ?, ?, ?, ?)",
        PROCESSES,
    )
    conn.executemany(
        "INSERT INTO process_steps (process_id, step_number, title, description, required_documents) VALUES (?, ?, ?, ?, ?)",
        PROCESS_STEPS,
    )
    conn.executemany(
        "INSERT INTO faqs (process_id, question, answer, last_verified_date, verified_by) VALUES (?, ?, ?, ?, ?)",
        [(pid, q, a, VERIFIED_DATE, SOURCE) for (pid, q, a) in FAQS],
    )
    conn.executemany(
        "INSERT INTO stakeholders (role, department, program) VALUES (?, ?, ?)",
        [("student", "IT", "Software Engineering"), ("advisor", "IT", None), ("staff", "Registrar", None)],
    )

    conn.commit()
    conn.close()
    print(f"Database built at {DB_PATH} — {len(PROCESSES)} processes, {len(FAQS)} FAQs, sourced from {SOURCE}.")


if __name__ == "__main__":
    build()
