"""
Builds institutional_processes.db — a small relational database covering
institutional stakeholders and academic operations.

NOTE: The data below is SAMPLE data modeled on typical Omani university
procedures (OJT registration, course withdrawal, graduation clearance).
Replace with your real institution's data before using this in production —
never seed a live database with fabricated records.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "institutional_processes.db")

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

SEED = """
INSERT INTO stakeholders (role, department, program) VALUES
 ('student', 'IT', 'Software Engineering'),
 ('advisor', 'IT', NULL),
 ('staff', 'Registrar', NULL);

INSERT INTO processes (id, name, description, applies_to_role, responsible_office) VALUES
 (1, 'On-the-Job Training (OJT) Registration',
     'Register for the mandatory OJT placement required for graduation.',
     'student', 'Career Guidance & Placement Office'),
 (2, 'Course Withdrawal',
     'Withdraw from a registered course before the withdrawal deadline.',
     'student', 'Registrar'),
 (3, 'Graduation Clearance',
     'Confirm all academic and financial requirements are met before graduation.',
     'student', 'Registrar');

INSERT INTO process_steps (process_id, step_number, title, description, required_documents) VALUES
 (1, 1, 'Confirm eligibility', 'Student must have completed at least 120 credit hours.', 'Transcript'),
 (1, 2, 'Submit OJT application', 'Fill and submit the OJT application form to the Placement Office.', 'OJT Application Form, CV'),
 (1, 3, 'Host organization approval', 'Placement Office confirms and assigns a host organization.', NULL),
 (1, 4, 'Supervisor sign-off', 'Academic supervisor signs off on the placement before start date.', 'Signed Placement Agreement'),
 (2, 1, 'Check withdrawal deadline', 'Confirm the current semester withdrawal deadline has not passed.', NULL),
 (2, 2, 'Submit withdrawal form', 'Submit the course withdrawal form to the Registrar.', 'Course Withdrawal Form'),
 (2, 3, 'Advisor approval', 'Academic advisor must approve the withdrawal.', NULL),
 (3, 1, 'Financial clearance', 'Confirm no outstanding fees with Finance Office.', NULL),
 (3, 2, 'Academic clearance', 'Confirm all required courses and OJT are completed.', 'Final Transcript'),
 (3, 3, 'Submit clearance form', 'Submit the graduation clearance form to the Registrar.', 'Graduation Clearance Form');

INSERT INTO forms (process_id, form_name, form_location) VALUES
 (1, 'OJT Application Form', 'Student Portal > Forms > OJT Application'),
 (2, 'Course Withdrawal Form', 'Student Portal > Forms > Course Withdrawal'),
 (3, 'Graduation Clearance Form', 'Student Portal > Forms > Graduation Clearance');
INSERT INTO faqs (process_id, question, answer, last_verified_date, verified_by) VALUES
 (1, 'How many credit hours do I need before applying for OJT?',
     'You need at least 120 completed credit hours before submitting an OJT application.',
     '2026-09-01', 'Sample Advisor'),
 (2, 'What happens if I miss the withdrawal deadline?',
     'After the deadline, withdrawal is only possible with department head approval for documented emergencies.',
     '2026-09-01', 'Sample Advisor'),
 (3, 'Can I graduate with an outstanding fee balance?',
     'No. Financial clearance from the Finance Office is required before graduation clearance is issued.',
     '2026-09-01', 'Sample Advisor');
"""

def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.executescript(SEED)
    conn.commit()
    conn.close()
    print(f"Database built at {DB_PATH}")

if __name__ == "__main__":
    build()
