"""Idempotent seed script for NIET B.Tech CSE (Data Science) Semester-I.

Preloads:
- Exact NIET B.Tech CSE (DS) Semester-I curriculum (19 credits, 900 total marks;
  Compulsory Audit excluded from total).
- Exact course codes, CIE/ESE or PS/PE max marks, and unit/module syllabus structure.
- Reviewed question bank across core Sem-I modules for Classroom Challenge fallback.
- A demo student account (demo@niet.edu.in / NietDemo@2026) with sample CIE/PS
  marks and attendance records.
"""

from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.academic import (
    Assessment,
    AssessmentResult,
    AttendanceRecord,
    StudentProfile,
    Subject,
    UnitTopic,
    User,
)

NIET_PROGRAMME = "B.Tech CSE (Data Science)"
NIET_PERIOD = "Semester-I"
NIET_INSTITUTION = "Noida Institute of Engineering and Technology (NIET)"
NIET_GRADING_SCHEME = "NIET 900-Mark Credit System"

NIET_SEM1_SUBJECTS = [
    {
        "code": "CAS0103",
        "name": "Calculus and Linear Algebra",
        "credits": 4,
        "category": "theory",
        "internal_label": "CIE",
        "internal_max_marks": 50,
        "external_label": "ESE",
        "external_max_marks": 100,
        "total_max_marks": 150,
        "is_excluded_from_total": False,
        "modules": [
            "Matrices",
            "Differential Calculus-I",
            "Differential Calculus-II",
            "Multivariable Calculus",
            "Vector Calculus",
        ],
    },
    {
        "code": "CEC0101",
        "name": "Digital Electronics and IoT Systems",
        "credits": 3,
        "category": "theory",
        "internal_label": "CIE",
        "internal_max_marks": 50,
        "external_label": "ESE",
        "external_max_marks": 100,
        "total_max_marks": 150,
        "is_excluded_from_total": False,
        "modules": [
            "Number System & Boolean Algebra",
            "Combinational Logic Circuits",
            "Sequential Logic Circuits",
            "Synchronous & Asynchronous Circuits",
            "Introduction to IoT",
        ],
    },
    {
        "code": "CCSAI0101",
        "name": "Fundamentals of Artificial Intelligence",
        "credits": 2,
        "category": "theory",
        "internal_label": "CIE",
        "internal_max_marks": 50,
        "external_label": "ESE",
        "external_max_marks": 50,
        "total_max_marks": 100,
        "is_excluded_from_total": False,
        "modules": [
            "Introduction to AI",
            "Data Literacy & Analysis",
            "Compute, Analysis & Visualization",
            "Applications of AI",
        ],
    },
    {
        "code": "CCSE0151",
        "name": "C Programming",
        "credits": 2,
        "category": "practical",
        "internal_label": "PS",
        "internal_max_marks": 50,
        "external_label": "PE",
        "external_max_marks": 50,
        "total_max_marks": 100,
        "is_excluded_from_total": False,
        "modules": [
            "Intro to Algorithm & C",
            "Control Statement",
            "Array & Strings",
            "Structure, Union & DMA",
            "File Handling & OOP",
        ],
    },
    {
        "code": "CCSE0152",
        "name": "Web Designing",
        "credits": 1,
        "category": "practical",
        "internal_label": "PS",
        "internal_max_marks": 25,
        "external_label": "PE",
        "external_max_marks": 25,
        "total_max_marks": 50,
        "is_excluded_from_total": False,
        "modules": [
            "Intro to Websites & HTML",
            "Elements of HTML",
            "Concept of CSS",
            "Intro to JavaScript",
            "Web Hosting",
        ],
    },
    {
        "code": "CMB0101",
        "name": "Innovation and Entrepreneurship",
        "credits": 2,
        "category": "theory",
        "internal_label": "CIE",
        "internal_max_marks": 100,
        "external_label": "NONE",
        "external_max_marks": 0,
        "total_max_marks": 100,
        "is_excluded_from_total": False,
        "modules": [
            "Intro to Innovation",
            "Entrepreneurship Development",
            "Developing an MVP",
            "IPR",
            "Entrepreneurial Ecosystem",
        ],
    },
    {
        "code": "CASL0101",
        "name": "Foreign Language",
        "credits": 2,
        "category": "theory",
        "internal_label": "CIE",
        "internal_max_marks": 50,
        "external_label": "ESE",
        "external_max_marks": 50,
        "total_max_marks": 100,
        "is_excluded_from_total": False,
        "modules": [
            "Foundations & Script",
            "Everyday Vocabulary & Grammar",
            "Reading & Comprehension",
            "Conversational Practice",
            "Cultural & Workplace Communication",
        ],
    },
    {
        "code": "CEC0151",
        "name": "Digital Electronics Lab",
        "credits": 1,
        "category": "practical",
        "internal_label": "PS",
        "internal_max_marks": 25,
        "external_label": "PE",
        "external_max_marks": 25,
        "total_max_marks": 50,
        "is_excluded_from_total": False,
        "modules": [
            "Logic Gates & Boolean Verification",
            "Combinational Circuits Lab",
            "Flip-Flops & Counters",
            "Shift Registers & Sequential Design",
            "IoT Sensor Interfacing Demo",
        ],
    },
    {
        "code": "CABC0151",
        "name": "ABC Lab",
        "credits": 2,
        "category": "practical",
        "internal_label": "PS",
        "internal_max_marks": 50,
        "external_label": "PE",
        "external_max_marks": 50,
        "total_max_marks": 100,
        "is_excluded_from_total": False,
        "modules": [
            "Applied Computing Setup",
            "Data Handling & Problem Solving",
            "Algorithmic Workflows",
            "Mini-Project Implementation",
            "Technical Documentation & Viva",
        ],
    },
    {
        "code": "CAU0101",
        "name": "Compulsory Audit",
        "credits": 0,
        "category": "audit",
        "internal_label": "CIE",
        "internal_max_marks": 0,
        "external_label": "NONE",
        "external_max_marks": 0,
        "total_max_marks": 0,
        "is_excluded_from_total": True,
        "modules": [
            "Environmental & Civic Literacy",
            "Professional Ethics & Academic Integrity",
        ],
    },
]


REVIEWED_QUESTIONS = [
    # CAS0103
    {
        "code": "CAS0103",
        "module": "Matrices",
        "difficulty": "easy",
        "question_text": "What is the rank of an n x n identity matrix I_n?",
        "options": ["0", "1", "n", "n - 1"],
        "answer_key": "n",
        "explanation": "All n rows (and columns) of I_n are linearly independent, so rank(I_n) = n.",
    },
    {
        "code": "CAS0103",
        "module": "Matrices",
        "difficulty": "medium",
        "question_text": "If A is an orthogonal matrix, which identity always holds?",
        "options": ["A^T = A^-1", "A^2 = I", "det(A) = 0", "A + A^T = 0"],
        "answer_key": "A^T = A^-1",
        "explanation": "By definition, a square matrix A is orthogonal when A * A^T = A^T * A = I.",
    },
    {
        "code": "CAS0103",
        "module": "Differential Calculus-I",
        "difficulty": "medium",
        "question_text": "Leibniz's theorem is primarily used to find:",
        "options": [
            "The n-th derivative of a product of two functions",
            "The inverse of a square matrix",
            "Partial derivatives of implicit functions",
            "Line integrals along closed curves",
        ],
        "answer_key": "The n-th derivative of a product of two functions",
        "explanation": "Leibniz's rule generalizes the product rule to compute D^n(u*v) using binomial coefficients.",
    },
    {
        "code": "CAS0103",
        "module": "Differential Calculus-II",
        "difficulty": "medium",
        "question_text": "Taylor's series expands a smooth function f(x) around a point x = a using:",
        "options": [
            "Successive derivatives of f evaluated at a",
            "Eigenvalues of the Hessian matrix only",
            "Definite integrals over [0, 1]",
            "Fourier sine coefficients",
        ],
        "answer_key": "Successive derivatives of f evaluated at a",
        "explanation": "Taylor's formula expresses f(x) as sum_{n=0}^infinity f^(n)(a)/n! * (x - a)^n.",
    },
    {
        "code": "CAS0103",
        "module": "Multivariable Calculus",
        "difficulty": "medium",
        "question_text": "If u = f(x, y) is homogeneous of degree n, Euler's theorem states that x*(du/dx) + y*(du/dy) equals:",
        "options": ["n * u", "u / n", "0", "(n - 1) * u"],
        "answer_key": "n * u",
        "explanation": "Euler's theorem on homogeneous functions gives x*u_x + y*u_y = n*u.",
    },
    {
        "code": "CAS0103",
        "module": "Vector Calculus",
        "difficulty": "medium",
        "question_text": "Which vector differential operator measures the tendency of a vector field to swirl or rotate at a point?",
        "options": ["Curl", "Divergence", "Gradient", "Laplacian"],
        "answer_key": "Curl",
        "explanation": "The curl (nabla x F) measures local rotation/circulation of a 3D vector field.",
    },
    # CEC0101
    {
        "code": "CEC0101",
        "module": "Number System & Boolean Algebra",
        "difficulty": "easy",
        "question_text": "What is the 2's complement representation of -6 in 4-bit signed binary?",
        "options": ["1010", "1001", "0110", "1101"],
        "answer_key": "1010",
        "explanation": "+6 is 0110; 1's complement is 1001; adding 1 yields 1010.",
    },
    {
        "code": "CEC0101",
        "module": "Combinational Logic Circuits",
        "difficulty": "easy",
        "question_text": "A 4-to-1 multiplexer requires how many select lines?",
        "options": ["1", "2", "3", "4"],
        "answer_key": "2",
        "explanation": "An N-to-1 multiplexer requires log2(N) select lines, so 4-to-1 needs 2 select lines.",
    },
    {
        "code": "CEC0101",
        "module": "Sequential Logic Circuits",
        "difficulty": "medium",
        "question_text": "What distinguishes a sequential circuit from a combinational circuit?",
        "options": [
            "Output depends on present inputs and past state (memory)",
            "Output depends only on current input values",
            "It uses only NAND gates",
            "It cannot operate with a clock signal",
        ],
        "answer_key": "Output depends on present inputs and past state (memory)",
        "explanation": "Sequential circuits incorporate feedback/memory elements like latches or flip-flops.",
    },
    {
        "code": "CEC0101",
        "module": "Synchronous & Asynchronous Circuits",
        "difficulty": "medium",
        "question_text": "In a synchronous counter, how is the clock signal applied to the flip-flops?",
        "options": [
            "All flip-flops receive the common clock pulse simultaneously",
            "Only the LSB flip-flop receives the external clock",
            "No clock signal is used",
            "Each flip-flop uses a different frequency crystal",
        ],
        "answer_key": "All flip-flops receive the common clock pulse simultaneously",
        "explanation": "Synchronous counters clock all flip-flops together, eliminating ripple propagation delay.",
    },
    {
        "code": "CEC0101",
        "module": "Introduction to IoT",
        "difficulty": "easy",
        "question_text": "Which lightweight publish/subscribe messaging protocol is widely used in IoT telemetry?",
        "options": ["MQTT", "SMTP", "FTP", "POP3"],
        "answer_key": "MQTT",
        "explanation": "MQTT (Message Queuing Telemetry Transport) is designed for low-bandwidth, constrained IoT devices.",
    },
    # CCSAI0101
    {
        "code": "CCSAI0101",
        "module": "Introduction to AI",
        "difficulty": "easy",
        "question_text": "Which search strategy uses a heuristic function h(n) plus path cost g(n) to find an optimal path?",
        "options": ["A* Search", "Breadth-First Search", "Depth-First Search", "Random Walk"],
        "answer_key": "A* Search",
        "explanation": "A* evaluates nodes using f(n) = g(n) + h(n), guaranteeing optimality with an admissible heuristic.",
    },
    {
        "code": "CCSAI0101",
        "module": "Data Literacy & Analysis",
        "difficulty": "easy",
        "question_text": "Why do we split a dataset into training and held-out test sets?",
        "options": [
            "To evaluate generalization on unseen data and detect overfitting",
            "To double the number of available features",
            "To eliminate the need for data cleaning",
            "To guarantee 100% accuracy in production",
        ],
        "answer_key": "To evaluate generalization on unseen data and detect overfitting",
        "explanation": "Held-out evaluation measures how well a trained model generalizes beyond memorized training rows.",
    },
    {
        "code": "CCSAI0101",
        "module": "Compute, Analysis & Visualization",
        "difficulty": "medium",
        "question_text": "Which regression metric expresses the proportion of variance in the target explained by the model?",
        "options": ["R-squared (R^2)", "Confusion Matrix", "Precision", "Recall"],
        "answer_key": "R-squared (R^2)",
        "explanation": "R^2 measures explained variance; MAE and RMSE measure error magnitude in target units.",
    },
    {
        "code": "CCSAI0101",
        "module": "Applications of AI",
        "difficulty": "medium",
        "question_text": "In responsible academic AI systems, predicted exam scores should be communicated as:",
        "options": [
            "Estimates with uncertainty and limitations, never guaranteed grades",
            "Official university marks",
            "Fixed judgments about student ability",
            "Confidential scores hidden from the student",
        ],
        "answer_key": "Estimates with uncertainty and limitations, never guaranteed grades",
        "explanation": "Responsible AI requires transparent uncertainty, limitations, and non-deterministic framing.",
    },
    # CCSE0151
    {
        "code": "CCSE0151",
        "module": "Intro to Algorithm & C",
        "difficulty": "easy",
        "question_text": "Which header file must be included in C to use printf() and scanf()?",
        "options": ["<stdio.h>", "<stdlib.h>", "<string.h>", "<math.h>"],
        "answer_key": "<stdio.h>",
        "explanation": "Standard Input/Output declarations such as printf and scanf live in <stdio.h>.",
    },
    {
        "code": "CCSE0151",
        "module": "Control Statement",
        "difficulty": "easy",
        "question_text": "Which loop in C is guaranteed to execute its body at least once?",
        "options": ["do-while loop", "while loop", "for loop", "if-else block"],
        "answer_key": "do-while loop",
        "explanation": "A do-while loop checks its condition after executing the loop body.",
    },
    {
        "code": "CCSE0151",
        "module": "Array & Strings",
        "difficulty": "easy",
        "question_text": "In C, every standard string literal is terminated by which character?",
        "options": ["'\\0' (null character)", "'\\n' (newline)", "' ' (space)", "EOF"],
        "answer_key": "'\\0' (null character)",
        "explanation": "C strings are null-terminated char arrays ending with '\\0'.",
    },
    {
        "code": "CCSE0151",
        "module": "Structure, Union & DMA",
        "difficulty": "medium",
        "question_text": "How does a union differ from a struct in C?",
        "options": [
            "All union members share the same memory location",
            "A union cannot hold integer fields",
            "A struct allocates only 1 byte total",
            "Unions are dynamically allocated automatically",
        ],
        "answer_key": "All union members share the same memory location",
        "explanation": "In a union, all members overlap at the same base address, sized to the largest member.",
    },
    {
        "code": "CCSE0151",
        "module": "File Handling & OOP",
        "difficulty": "medium",
        "question_text": "Which C standard library function opens a file and returns a FILE pointer?",
        "options": ["fopen()", "fread()", "fclose()", "fseek()"],
        "answer_key": "fopen()",
        "explanation": "fopen(filename, mode) opens a stream and returns FILE* (or NULL on failure).",
    },
    # CCSE0152
    {
        "code": "CCSE0152",
        "module": "Elements of HTML",
        "difficulty": "easy",
        "question_text": "Which HTML5 element is semantic for the primary navigation links of a page?",
        "options": ["<nav>", "<div>", "<span>", "<br>"],
        "answer_key": "<nav>",
        "explanation": "<nav> explicitly identifies major navigation blocks for browsers and screen readers.",
    },
    {
        "code": "CCSE0152",
        "module": "Concept of CSS",
        "difficulty": "easy",
        "question_text": "In the CSS box model, which property creates space outside an element's border?",
        "options": ["margin", "padding", "border-width", "outline-offset"],
        "answer_key": "margin",
        "explanation": "Margin sits outside the border, whereas padding sits between content and border.",
    },
    {
        "code": "CCSE0152",
        "module": "Intro to JavaScript",
        "difficulty": "easy",
        "question_text": "Which DOM method selects the first element matching a CSS selector?",
        "options": ["document.querySelector()", "document.getElementsByTagName()", "document.write()", "window.alert()"],
        "answer_key": "document.querySelector()",
        "explanation": "querySelector returns the first Element within the document that matches the selector.",
    },
    # CMB0101
    {
        "code": "CMB0101",
        "module": "Developing an MVP",
        "difficulty": "easy",
        "question_text": "What is the primary purpose of a Minimum Viable Product (MVP)?",
        "options": [
            "Validate core user value quickly with minimal build effort and gather feedback",
            "Release every planned future feature before testing with users",
            "Skip user research and focus only on visual polish",
            "Avoid measuring customer adoption",
        ],
        "answer_key": "Validate core user value quickly with minimal build effort and gather feedback",
        "explanation": "An MVP tests key hypotheses with real users at the lowest sustainable cost.",
    },
    {
        "code": "CMB0101",
        "module": "IPR",
        "difficulty": "medium",
        "question_text": "Which form of Intellectual Property protects an original invention that solves a technical problem?",
        "options": ["Patent", "Trademark", "Copyright", "Trade Secret"],
        "answer_key": "Patent",
        "explanation": "Patents grant time-limited exclusive rights for novel, non-obvious, useful inventions.",
    },
    {
        "code": "CMB0101",
        "module": "Entrepreneurial Ecosystem",
        "difficulty": "medium",
        "question_text": "Which framework evaluates Strengths, Weaknesses, Opportunities, and Threats?",
        "options": ["SWOT analysis", "PESTLE analysis", "SCAMPER", "Kanban"],
        "answer_key": "SWOT analysis",
        "explanation": "SWOT evaluates internal strengths/weaknesses alongside external opportunities/threats.",
    },
]


def seed_database(db: Session) -> dict:
    """Seed NIET Sem-I subjects, units, reviewed questions, and demo student."""
    subjects_created = 0
    units_created = 0
    questions_created = 0

    code_to_subject: dict[str, Subject] = {}
    module_lookup: dict[tuple[str, str], UnitTopic] = {}

    for spec in NIET_SEM1_SUBJECTS:
        subj = db.scalar(
            select(Subject).where(
                Subject.user_id.is_(None),
                Subject.programme == NIET_PROGRAMME,
                Subject.academic_period == NIET_PERIOD,
                Subject.code == spec["code"],
            )
        )
        if not subj:
            subj = Subject(
                user_id=None,
                programme=NIET_PROGRAMME,
                academic_period=NIET_PERIOD,
                code=spec["code"],
                name=spec["name"],
                credits=spec["credits"],
                category=spec["category"],
                internal_label=spec["internal_label"],
                internal_max_marks=spec["internal_max_marks"],
                external_label=spec["external_label"],
                external_max_marks=spec["external_max_marks"],
                total_max_marks=spec["total_max_marks"],
                is_excluded_from_total=spec["is_excluded_from_total"],
            )
            db.add(subj)
            db.flush()
            subjects_created += 1

        code_to_subject[spec["code"]] = subj

        existing_units = {
            u.title: u
            for u in db.scalars(select(UnitTopic).where(UnitTopic.subject_id == subj.id)).all()
        }
        for idx, mod_title in enumerate(spec["modules"], start=1):
            unit = existing_units.get(mod_title)
            if not unit:
                unit = UnitTopic(
                    subject_id=subj.id,
                    parent_id=None,
                    order_index=idx,
                    node_type="unit",
                    title=mod_title,
                    description=f"Module {idx} of {spec['code']} ({spec['name']})",
                )
                db.add(unit)
                db.flush()
                units_created += 1
            module_lookup[(spec["code"], mod_title)] = unit

    # Seed demo student with sample NIET Sem-I marks & attendance
    demo_user = db.scalar(select(User).where(User.email == "demo@niet.edu.in"))
    if not demo_user:
        demo_user = User(
            name="Aarav Sharma (NIET Demo)",
            email="demo@niet.edu.in",
            password_hash=hash_password("NietDemo@2026"),
            role="student",
            is_demo=True,
        )
        db.add(demo_user)
        db.flush()

        profile = StudentProfile(
            user_id=demo_user.id,
            education_level="undergraduate",
            institution=NIET_INSTITUTION,
            programme=NIET_PROGRAMME,
            academic_period=NIET_PERIOD,
            grading_scheme=NIET_GRADING_SCHEME,
            demo_identifier="DEMO-CSDS-01",
            weekly_study_hours=16.0,
        )
        db.add(profile)

        sample_marks = [
            ("CAS0103", "CIE-1 Unit Test", "CIE", 50.0, 39.0, date(2026, 9, 18), 6.5),
            ("CEC0101", "CIE-1 Digital & IoT", "CIE", 50.0, 34.0, date(2026, 9, 21), 4.0),
            ("CCSAI0101", "CIE-1 AI Foundations", "CIE", 50.0, 43.0, date(2026, 9, 24), 5.0),
            ("CCSE0151", "PS-1 C Lab Evaluation", "PS", 50.0, 44.0, date(2026, 10, 5), 5.5),
            ("CCSE0152", "PS-1 Web Design Lab", "PS", 25.0, 22.0, date(2026, 10, 8), 3.0),
            ("CMB0101", "CIE-1 Innovation Pitch", "CIE", 100.0, 81.0, date(2026, 10, 14), 4.5),
            ("CASL0101", "CIE-1 Language Assessment", "CIE", 50.0, 38.0, date(2026, 10, 17), 2.5),
            ("CEC0151", "PS-1 Digital Lab", "PS", 25.0, 20.0, date(2026, 10, 21), 2.0),
            ("CABC0151", "PS-1 ABC Lab Review", "PS", 50.0, 42.0, date(2026, 10, 25), 3.5),
        ]
        for code, title, a_type, max_m, obt_m, a_date, hrs in sample_marks:
            subj = code_to_subject[code]
            assessment = Assessment(
                subject_id=subj.id,
                user_id=demo_user.id,
                title=title,
                assessment_type=a_type,
                max_marks=max_m,
                assessment_date=a_date,
                academic_period=NIET_PERIOD,
            )
            db.add(assessment)
            db.flush()
            db.add(
                AssessmentResult(
                    student_id=demo_user.id,
                    assessment_id=assessment.id,
                    marks_obtained=obt_m,
                    grading_scheme_snapshot=NIET_GRADING_SCHEME,
                    study_hours_logged=hrs,
                    notes="Preloaded NIET Semester-I demo internal assessment",
                )
            )

        sample_attendance = [
            ("CAS0103", 28, 32),
            ("CEC0101", 21, 30),
            ("CCSAI0101", 23, 25),
            ("CCSE0151", 19, 20),
            ("CCSE0152", 13, 15),
            ("CMB0101", 18, 22),
            ("CASL0101", 17, 20),
            ("CEC0151", 11, 14),
            ("CABC0151", 18, 20),
        ]
        for code, attended, total in sample_attendance:
            subj = code_to_subject[code]
            db.add(
                AttendanceRecord(
                    student_id=demo_user.id,
                    subject_id=subj.id,
                    academic_period=NIET_PERIOD,
                    classes_attended=attended,
                    total_classes=total,
                    recorded_date=date(2026, 11, 20),
                )
            )

    db.commit()
    return {
        "subjects_created": subjects_created,
        "units_created": units_created,
        "total_subjects": len(NIET_SEM1_SUBJECTS),
        "total_credits": sum(s["credits"] for s in NIET_SEM1_SUBJECTS),
        "total_marks": sum(
            s["total_max_marks"] for s in NIET_SEM1_SUBJECTS if not s["is_excluded_from_total"]
        ),
    }


def main() -> None:
    from seed_classroom_questions import seed_classroom_questions

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        summary = seed_database(db)
        q_summary = seed_classroom_questions(db)
        print("NIET Sem-I seed complete:", {**summary, **q_summary})


if __name__ == "__main__":
    main()
