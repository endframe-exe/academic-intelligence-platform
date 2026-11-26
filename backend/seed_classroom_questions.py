"""Verified preloaded question bank for NIET B.Tech CSE (DS) Semester-I Classroom Challenge.

Provides 10 syllabus-grounded MCQs + explanations for each of the 6 core Sem-I subjects
(60 questions total):
- CAS0103: Calculus and Linear Algebra (Matrices & Calculus)
- CEC0101: Digital Electronics and IoT Systems (Boolean Algebra & Logic Gates)
- CCSAI0101: Fundamentals of Artificial Intelligence (Intro to AI & Data Literacy)
- CCSE0151: C Programming (C Control Statements & Arrays)
- CCSE0152: Web Designing (HTML/CSS/JS)
- CMB0101: Innovation and Entrepreneurship (Innovation, SCAMPER & SWOT)
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.models.academic import Question, Subject, UnitTopic
from seed_niet_sem1 import NIET_PERIOD, NIET_PROGRAMME, seed_database

CLASSROOM_QUESTION_BANK: list[dict] = [
    # =========================================================================
    # CAS0103 — Calculus and Linear Algebra (10 Questions)
    # =========================================================================
    {
        "code": "CAS0103",
        "module": "Matrices",
        "difficulty": "easy",
        "question_text": "What is the rank of an n x n identity matrix I_n?",
        "options": ["0", "1", "n", "n - 1"],
        "answer_key": "n",
        "explanation": "All n rows and columns of I_n are linearly independent, so rank(I_n) = n.",
    },
    {
        "code": "CAS0103",
        "module": "Matrices",
        "difficulty": "medium",
        "question_text": "If A is an orthogonal matrix, which identity always holds?",
        "options": ["A^T = A^-1", "A^2 = I", "det(A) = 0", "A + A^T = 0"],
        "answer_key": "A^T = A^-1",
        "explanation": "By definition, a real square matrix A is orthogonal when A * A^T = A^T * A = I.",
    },
    {
        "code": "CAS0103",
        "module": "Matrices",
        "difficulty": "medium",
        "question_text": "According to the Cayley-Hamilton theorem, every square matrix satisfies:",
        "options": [
            "Its own characteristic equation",
            "A = A^T",
            "det(A) = trace(A)",
            "rank(A) = 0",
        ],
        "answer_key": "Its own characteristic equation",
        "explanation": "Replacing lambda by A in det(A - lambda*I) = 0 yields the zero matrix.",
    },
    {
        "code": "CAS0103",
        "module": "Matrices",
        "difficulty": "hard",
        "question_text": "For a consistent system AX = B with n unknowns and rank(A) = r < n, how many linearly independent parameters appear in the general solution?",
        "options": ["n - r", "r", "n + r", "0"],
        "answer_key": "n - r",
        "explanation": "By the Rank-Nullity theorem, the solution space has dimension nullity(A) = n - r.",
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
        "explanation": "Leibniz's rule generalizes the product rule to compute D^n(u*v) via binomial coefficients.",
    },
    {
        "code": "CAS0103",
        "module": "Differential Calculus-I",
        "difficulty": "easy",
        "question_text": "Rolle's theorem requires f(x) on [a, b] to be continuous on [a, b], differentiable on (a, b), and satisfy:",
        "options": ["f(a) = f(b)", "f'(a) = f'(b)", "f(a) + f(b) = 0", "f''(x) = 0"],
        "answer_key": "f(a) = f(b)",
        "explanation": "When f(a) = f(b) under continuity and differentiability, there exists c in (a, b) with f'(c) = 0.",
    },
    {
        "code": "CAS0103",
        "module": "Differential Calculus-II",
        "difficulty": "medium",
        "question_text": "Maclaurin's series is a special case of Taylor's series expanded around which point?",
        "options": ["x = 0", "x = 1", "x = pi", "x = infinity"],
        "answer_key": "x = 0",
        "explanation": "Maclaurin's series sets the expansion center a = 0 in Taylor's theorem.",
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
        "module": "Multivariable Calculus",
        "difficulty": "hard",
        "question_text": "For u = f(x, y) and v = g(x, y), the Jacobian J = partial(u, v) / partial(x, y) vanishes identically when:",
        "options": [
            "u and v are functionally dependent",
            "u and v are linear functions",
            "u_x = v_y",
            "f and g are continuous",
        ],
        "answer_key": "u and v are functionally dependent",
        "explanation": "A zero Jacobian determinant over a region indicates functional dependence between u and v.",
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

    # =========================================================================
    # CEC0101 — Digital Electronics and IoT Systems (10 Questions)
    # =========================================================================
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
        "module": "Number System & Boolean Algebra",
        "difficulty": "easy",
        "question_text": "Which pair of gates are individually called Universal Logic Gates?",
        "options": [
            "NAND and NOR",
            "AND and OR",
            "XOR and XNOR",
            "NOT and Buffer",
        ],
        "answer_key": "NAND and NOR",
        "explanation": "Any Boolean function can be implemented using only NAND gates or only NOR gates.",
    },
    {
        "code": "CEC0101",
        "module": "Number System & Boolean Algebra",
        "difficulty": "medium",
        "question_text": "By De Morgan's theorem, the expression (A + B)' simplifies to:",
        "options": ["A' . B'", "A' + B'", "A . B", "(A . B)'"],
        "answer_key": "A' . B'",
        "explanation": "De Morgan's law states that the complement of a sum equals the product of the complements.",
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
        "module": "Combinational Logic Circuits",
        "difficulty": "medium",
        "question_text": "What are the two outputs of a Half Adder circuit for inputs A and B?",
        "options": [
            "Sum = A XOR B, Carry = A AND B",
            "Sum = A AND B, Carry = A XOR B",
            "Sum = A OR B, Carry = A NAND B",
            "Sum = A XNOR B, Carry = A NOR B",
        ],
        "answer_key": "Sum = A XOR B, Carry = A AND B",
        "explanation": "A half adder produces Sum = A ^ B and Carry = A . B.",
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
        "module": "Sequential Logic Circuits",
        "difficulty": "hard",
        "question_text": "In a JK flip-flop, what occurs when J = 1 and K = 1 on an active clock edge?",
        "options": [
            "The output toggles (Q_next = Q')",
            "The output resets to 0",
            "The output sets to 1",
            "An invalid/forbidden state occurs",
        ],
        "answer_key": "The output toggles (Q_next = Q')",
        "explanation": "Unlike SR flip-flops, J=K=1 resolves the forbidden state by toggling Q.",
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
        "module": "Synchronous & Asynchronous Circuits",
        "difficulty": "medium",
        "question_text": "How many flip-flops are required to build a MOD-16 binary counter?",
        "options": ["4", "8", "16", "2"],
        "answer_key": "4",
        "explanation": "A MOD-2^n counter requires n flip-flops; since 16 = 2^4, 4 flip-flops are needed.",
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

    # =========================================================================
    # CCSAI0101 — Fundamentals of Artificial Intelligence (10 Questions)
    # =========================================================================
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
        "module": "Introduction to AI",
        "difficulty": "easy",
        "question_text": "In the Turing Test, a machine demonstrates intelligence if:",
        "options": [
            "A human interrogator cannot reliably distinguish it from a human via text conversation",
            "It solves differential equations faster than a calculator",
            "It passes a hardware benchmark",
            "It stores more than 1 TB of data",
        ],
        "answer_key": "A human interrogator cannot reliably distinguish it from a human via text conversation",
        "explanation": "Alan Turing's imitation game evaluates conversational indistinguishability from a human.",
    },
    {
        "code": "CCSAI0101",
        "module": "Introduction to AI",
        "difficulty": "medium",
        "question_text": "Which learning paradigm trains an agent via rewards and penalties from interacting with an environment?",
        "options": [
            "Reinforcement Learning",
            "Unsupervised Clustering",
            "Dimensionality Reduction",
            "Association Rule Mining",
        ],
        "answer_key": "Reinforcement Learning",
        "explanation": "Reinforcement learning optimizes a policy to maximize cumulative reward from environment feedback.",
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
        "module": "Data Literacy & Analysis",
        "difficulty": "medium",
        "question_text": "What is data leakage in a machine learning pipeline?",
        "options": [
            "Using information from validation/test records or future targets during training",
            "Compressing CSV files before upload",
            "Normalizing features on the training fold only",
            "Removing duplicate rows from raw data",
        ],
        "answer_key": "Using information from validation/test records or future targets during training",
        "explanation": "Data leakage inflates evaluation metrics artificially because the model sees test-side information.",
    },
    {
        "code": "CCSAI0101",
        "module": "Data Literacy & Analysis",
        "difficulty": "easy",
        "question_text": "Which measure of central tendency is least sensitive to extreme outliers?",
        "options": ["Median", "Arithmetic Mean", "Range", "Variance"],
        "answer_key": "Median",
        "explanation": "The median depends only on middle rank ordering rather than extreme outlier magnitudes.",
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
        "module": "Compute, Analysis & Visualization",
        "difficulty": "medium",
        "question_text": "For imbalanced classification, which single metric balances Precision and Recall via their harmonic mean?",
        "options": ["F1-score", "Accuracy", "Mean Absolute Error", "R-squared"],
        "answer_key": "F1-score",
        "explanation": "F1 = 2 * (Precision * Recall) / (Precision + Recall), penalizing extreme imbalance between them.",
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
    {
        "code": "CCSAI0101",
        "module": "Applications of AI",
        "difficulty": "easy",
        "question_text": "Retrieval-Augmented Generation (RAG) improves LLM question generation by:",
        "options": [
            "Supplying relevant passages from approved syllabus documents as context",
            "Retraining LLM weights from scratch on every upload",
            "Disabling source verification",
            "Scraping random websites without review",
        ],
        "answer_key": "Supplying relevant passages from approved syllabus documents as context",
        "explanation": "RAG grounds generation in retrieved source text rather than relying solely on parametric memory.",
    },

    # =========================================================================
    # CCSE0151 — C Programming (10 Questions)
    # =========================================================================
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
        "module": "Intro to Algorithm & C",
        "difficulty": "easy",
        "question_text": "In C, which operator returns the memory address of a variable?",
        "options": ["& (address-of)", "* (dereference)", "->", "%"],
        "answer_key": "& (address-of)",
        "explanation": "The unary & operator yields the memory address of its operand.",
    },
    {
        "code": "CCSE0151",
        "module": "Control Statement",
        "difficulty": "easy",
        "question_text": "Which loop in C is guaranteed to execute its body at least once?",
        "options": ["do-while loop", "while loop", "for loop", "if-else block"],
        "answer_key": "do-while loop",
        "explanation": "A do-while loop evaluates its continuation condition after executing the loop body.",
    },
    {
        "code": "CCSE0151",
        "module": "Control Statement",
        "difficulty": "medium",
        "question_text": "What happens if a switch-case block omits the 'break' statement after a matching case?",
        "options": [
            "Execution falls through into subsequent case blocks",
            "The compiler rejects the program",
            "The program terminates immediately",
            "Only the default block runs",
        ],
        "answer_key": "Execution falls through into subsequent case blocks",
        "explanation": "Without break, C continues executing statements sequentially into the following cases.",
    },
    {
        "code": "CCSE0151",
        "module": "Control Statement",
        "difficulty": "easy",
        "question_text": "Which statement skips the remainder of the current loop iteration and jumps to the next iteration?",
        "options": ["continue", "break", "goto", "return"],
        "answer_key": "continue",
        "explanation": "continue skips the rest of the current iteration, whereas break exits the loop entirely.",
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
        "module": "Array & Strings",
        "difficulty": "medium",
        "question_text": "For an array `int arr[5] = {10, 20, 30, 40, 50};`, what is the valid index range in C?",
        "options": ["0 to 4", "1 to 5", "0 to 5", "-1 to 4"],
        "answer_key": "0 to 4",
        "explanation": "C arrays are zero-indexed, so an array of size N has valid indices 0 through N - 1.",
    },
    {
        "code": "CCSE0151",
        "module": "Array & Strings",
        "difficulty": "medium",
        "question_text": "Which <string.h> function compares two strings lexicographically and returns 0 if equal?",
        "options": ["strcmp()", "strcpy()", "strcat()", "strlen()"],
        "answer_key": "strcmp()",
        "explanation": "strcmp(s1, s2) returns 0 when both null-terminated strings have identical characters.",
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
        "explanation": "fopen(filename, mode) opens a file stream and returns FILE* (or NULL on failure).",
    },

    # =========================================================================
    # CCSE0152 — Web Designing (10 Questions)
    # =========================================================================
    {
        "code": "CCSE0152",
        "module": "Intro to Websites & HTML",
        "difficulty": "easy",
        "question_text": "What does the <!DOCTYPE html> declaration at the top of an HTML document specify?",
        "options": [
            "Instructs the browser to parse the document in HTML5 standards mode",
            "Links an external CSS stylesheet",
            "Executes JavaScript before rendering",
            "Defines the page character encoding as ASCII",
        ],
        "answer_key": "Instructs the browser to parse the document in HTML5 standards mode",
        "explanation": "<!DOCTYPE html> triggers standards-compliant HTML5 rendering instead of quirks mode.",
    },
    {
        "code": "CCSE0152",
        "module": "Intro to Websites & HTML",
        "difficulty": "easy",
        "question_text": "Which protocol is standard for encrypted communication between a web browser and server?",
        "options": ["HTTPS", "FTP", "Telnet", "SMTP"],
        "answer_key": "HTTPS",
        "explanation": "HTTPS layers HTTP over TLS encryption to protect confidentiality and integrity.",
    },
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
        "module": "Elements of HTML",
        "difficulty": "easy",
        "question_text": "Why is the `alt` attribute important on an HTML <img> element?",
        "options": [
            "Provides accessible text for screen readers and displays if the image fails to load",
            "Sets the image border color",
            "Compresses the image file size",
            "Makes the image clickable automatically",
        ],
        "answer_key": "Provides accessible text for screen readers and displays if the image fails to load",
        "explanation": "The alt attribute ensures accessibility compliance and graceful fallback text.",
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
        "module": "Concept of CSS",
        "difficulty": "medium",
        "question_text": "Among these CSS selectors, which has the highest specificity?",
        "options": ["#header-nav", ".nav-link", "nav", "*"],
        "answer_key": "#header-nav",
        "explanation": "An ID selector (#header-nav) has higher specificity (0,1,0,0) than classes, elements, or *.",
    },
    {
        "code": "CCSE0152",
        "module": "Concept of CSS",
        "difficulty": "medium",
        "question_text": "Which CSS layout property turns an element into a one-dimensional flex container?",
        "options": ["display: flex", "position: sticky", "float: left", "overflow: hidden"],
        "answer_key": "display: flex",
        "explanation": "display: flex enables Flexbox alignment along main and cross axes.",
    },
    {
        "code": "CCSE0152",
        "module": "Intro to JavaScript",
        "difficulty": "easy",
        "question_text": "Which DOM method selects the first element matching a CSS selector?",
        "options": [
            "document.querySelector()",
            "document.getElementsByTagName()",
            "document.write()",
            "window.alert()",
        ],
        "answer_key": "document.querySelector()",
        "explanation": "querySelector returns the first Element within the document matching the given selector.",
    },
    {
        "code": "CCSE0152",
        "module": "Intro to JavaScript",
        "difficulty": "medium",
        "question_text": "In JavaScript, how does `===` differ from `==`?",
        "options": [
            "`===` checks strict equality without type coercion",
            "`===` only compares strings",
            "`==` performs assignment",
            "There is no difference",
        ],
        "answer_key": "`===` checks strict equality without type coercion",
        "explanation": "Strict equality (===) compares both type and value, avoiding implicit type conversion.",
    },
    {
        "code": "CCSE0152",
        "module": "Web Hosting",
        "difficulty": "easy",
        "question_text": "What is the role of DNS (Domain Name System) when hosting a website?",
        "options": [
            "Translates human-readable domain names into IP addresses",
            "Compiles TypeScript into CSS",
            "Stores relational database tables",
            "Renders SVG graphics on the GPU",
        ],
        "answer_key": "Translates human-readable domain names into IP addresses",
        "explanation": "DNS resolves domain names such as example.edu into routable server IP addresses.",
    },

    # =========================================================================
    # CMB0101 — Innovation and Entrepreneurship (10 Questions)
    # =========================================================================
    {
        "code": "CMB0101",
        "module": "Intro to Innovation",
        "difficulty": "easy",
        "question_text": "In the SCAMPER ideation framework, what does the letter 'S' stand for?",
        "options": ["Substitute", "Standardize", "Simplify", "Stabilize"],
        "answer_key": "Substitute",
        "explanation": "SCAMPER stands for Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",
    },
    {
        "code": "CMB0101",
        "module": "Intro to Innovation",
        "difficulty": "medium",
        "question_text": "In Design Thinking, which phase focuses on understanding user pain points before defining the problem?",
        "options": ["Empathize", "Prototype", "Test", "Deploy"],
        "answer_key": "Empathize",
        "explanation": "The five Design Thinking stages start with Empathize -> Define -> Ideate -> Prototype -> Test.",
    },
    {
        "code": "CMB0101",
        "module": "Intro to Innovation",
        "difficulty": "medium",
        "question_text": "How does incremental innovation differ from disruptive innovation?",
        "options": [
            "Incremental improves existing solutions steadily; disruptive creates a new market or value network",
            "Incremental always fails; disruptive requires zero customers",
            "Disruptive only applies to hardware patents",
            "They are identical terms",
        ],
        "answer_key": "Incremental improves existing solutions steadily; disruptive creates a new market or value network",
        "explanation": "Incremental innovation refines current offerings, whereas disruptive innovation transforms market access.",
    },
    {
        "code": "CMB0101",
        "module": "Entrepreneurship Development",
        "difficulty": "easy",
        "question_text": "Which strategic matrix evaluates internal Strengths/Weaknesses alongside external Opportunities/Threats?",
        "options": ["SWOT analysis", "PESTLE analysis", "Gantt chart", "PERT chart"],
        "answer_key": "SWOT analysis",
        "explanation": "SWOT organizes internal factors (Strengths, Weaknesses) and external factors (Opportunities, Threats).",
    },
    {
        "code": "CMB0101",
        "module": "Entrepreneurship Development",
        "difficulty": "medium",
        "question_text": "In PESTLE analysis, what does the 'L' represent?",
        "options": ["Legal", "Logistics", "Leadership", "Liquidity"],
        "answer_key": "Legal",
        "explanation": "PESTLE scans Political, Economic, Social, Technological, Legal, and Environmental macro factors.",
    },
    {
        "code": "CMB0101",
        "module": "Developing an MVP",
        "difficulty": "easy",
        "question_text": "What is the primary purpose of a Minimum Viable Product (MVP)?",
        "options": [
            "Validate core user value quickly with minimal build effort and gather real feedback",
            "Release every planned future feature before testing with users",
            "Skip user research and focus only on visual polish",
            "Avoid measuring user engagement",
        ],
        "answer_key": "Validate core user value quickly with minimal build effort and gather real feedback",
        "explanation": "An MVP tests critical product hypotheses with real users at minimal initial cost.",
    },
    {
        "code": "CMB0101",
        "module": "Developing an MVP",
        "difficulty": "medium",
        "question_text": "What is a 'Value Proposition' in a Business Model Canvas?",
        "options": [
            "The specific bundle of benefits solving a customer segment's problem",
            "The office lease agreement",
            "The server hosting bill",
            "Employee attendance policy",
        ],
        "answer_key": "The specific bundle of benefits solving a customer segment's problem",
        "explanation": "Value Proposition describes why target users choose the product over alternatives.",
    },
    {
        "code": "CMB0101",
        "module": "IPR",
        "difficulty": "medium",
        "question_text": "Which form of Intellectual Property protects an original technical invention that solves a specific problem?",
        "options": ["Patent", "Trademark", "Copyright", "Trade Secret"],
        "answer_key": "Patent",
        "explanation": "Patents grant time-limited exclusive rights for novel, non-obvious, useful technical inventions.",
    },
    {
        "code": "CMB0101",
        "module": "IPR",
        "difficulty": "easy",
        "question_text": "Which Intellectual Property mechanism protects a brand logo, wordmark, or distinctive sign?",
        "options": ["Trademark", "Patent", "Industrial Design", "Geographical Indication"],
        "answer_key": "Trademark",
        "explanation": "Trademarks distinguish the commercial source of goods or services.",
    },
    {
        "code": "CMB0101",
        "module": "Entrepreneurial Ecosystem",
        "difficulty": "medium",
        "question_text": "What is the primary role of a campus technology incubator for early-stage student startups?",
        "options": [
            "Provide mentorship, workspace, validation support, and ecosystem connections",
            "Guarantee stock-market IPOs within one month",
            "Replace academic degree requirements",
            "Eliminate the need for customer discovery",
        ],
        "answer_key": "Provide mentorship, workspace, validation support, and ecosystem connections",
        "explanation": "Incubators help early founders de-risk ideas through mentoring, infrastructure, and networks.",
    },
]


def seed_classroom_questions(db: Session) -> dict:
    """Ensure NIET Sem-I subjects exist, then upsert all 60 Classroom Challenge MCQs."""
    seed_database(db)

    subjects = db.scalars(
        select(Subject).where(
            Subject.user_id.is_(None),
            Subject.programme == NIET_PROGRAMME,
            Subject.academic_period == NIET_PERIOD,
        )
    ).all()
    code_to_subject = {s.code: s for s in subjects}

    module_lookup: dict[tuple[str, str], UnitTopic] = {}
    for subj in subjects:
        units = db.scalars(select(UnitTopic).where(UnitTopic.subject_id == subj.id)).all()
        for u in units:
            module_lookup[(subj.code, u.title)] = u

    inserted = 0
    updated = 0
    for item in CLASSROOM_QUESTION_BANK:
        subj = code_to_subject[item["code"]]
        unit = module_lookup.get((item["code"], item["module"]))
        existing = db.scalar(
            select(Question).where(
                Question.subject_id == subj.id,
                Question.question_text == item["question_text"],
            )
        )
        if existing:
            existing.unit_id = unit.id if unit else existing.unit_id
            existing.difficulty = item["difficulty"]
            existing.options_json = item["options"]
            existing.answer_key = item["answer_key"]
            existing.explanation = item["explanation"]
            existing.source = "reviewed_bank"
            existing.is_reviewed = True
            updated += 1
        else:
            db.add(
                Question(
                    subject_id=subj.id,
                    unit_id=unit.id if unit else None,
                    syllabus_document_id=None,
                    question_type="mcq",
                    difficulty=item["difficulty"],
                    question_text=item["question_text"],
                    options_json=item["options"],
                    answer_key=item["answer_key"],
                    explanation=item["explanation"],
                    source="reviewed_bank",
                    is_reviewed=True,
                )
            )
            inserted += 1

    db.commit()
    return {
        "total_bank_questions": len(CLASSROOM_QUESTION_BANK),
        "inserted": inserted,
        "updated": updated,
    }


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        summary = seed_classroom_questions(db)
        print("Classroom Challenge question bank seeded:", summary)


if __name__ == "__main__":
    main()
