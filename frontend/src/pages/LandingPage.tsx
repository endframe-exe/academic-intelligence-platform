import { useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { AcademicSignalSvg } from "../components/AcademicSignalSvg";
import { CardSwap, type EditorialCardItem } from "../components/ui/CardSwap";
import { usePrefersReducedMotion } from "../lib/utils";

gsap.registerPlugin(ScrollTrigger);

const MODULE_CARDS: EditorialCardItem[] = [
  {
    code: "MOD-01",
    category: "Academic Intelligence",
    title: "Structured Records & NIET 900-Mark Ledger",
    summary:
      "Track CIE, ESE, Practical Sessional (PS), Practical External (PE), and attendance in one validated ledger with CSV import preview.",
    metricsLabel: "19 Credits · 900 Marks · Audit Excluded",
    route: "/academics",
  },
  {
    code: "MOD-02",
    category: "Performance Prediction",
    title: "Validated Baseline Estimators with Uncertainty",
    summary:
      "Ridge Regression and Random Forest candidates evaluated on held-out splits with MAE, RMSE, R², and a >=3 assessment sufficiency gate.",
    metricsLabel: "Estimates only · Never guaranteed grades",
    route: "/predictions",
  },
  {
    code: "MOD-03",
    category: "Study Intelligence",
    title: "Evidence-Linked Study Schedule Allocation",
    summary:
      "Transparent priority rules combine credit weight, recorded marks, and attendance thresholds with optional Gemini 2.5 Flash synthesis.",
    metricsLabel: "Editable weekly hours · Rule fallback",
    route: "/study-planner",
  },
  {
    code: "MOD-04",
    category: "Syllabus Intelligence & Assessment Lab",
    title: "Gemini Syllabus Lab & QR Classroom Challenge",
    summary:
      "Upload PDF/DOCX syllabi, review extracted modules, generate grounded MCQs via Gemini 2.5 Flash, or launch the mobile Classroom Challenge.",
    metricsLabel: "Preloaded NIET CSE (DS) Sem-I",
    route: "/classroom-challenge",
  },
];

const WORDMARK_LETTERS = ["S", "C", "H", "O", "L", "I", "A"];

export function LandingPage() {
  const pageRef = useRef<HTMLDivElement>(null);
  const wordmarkRef = useRef<HTMLDivElement>(null);
  const motifRef = useRef<HTMLDivElement>(null);
  const reducedMotion = usePrefersReducedMotion();
  const navigate = useNavigate();

  useEffect(() => {
    if (reducedMotion || !pageRef.current) return;

    const ctx = gsap.context(() => {
      // Reveal wordmark on initial load & animate outward letter-spacing + translation across 700px scroll
      if (wordmarkRef.current) {
        const letters = Array.from(wordmarkRef.current.children) as HTMLElement[];
        gsap.from(letters, {
          y: 22,
          opacity: 0,
          duration: 0.75,
          stagger: 0.045,
          ease: "power3.out",
          clearProps: "opacity",
        });

        const mid = (letters.length - 1) / 2;
        letters.forEach((letter, idx) => {
          const offsetFromCenter = idx - mid;
          gsap.to(letter, {
            x: offsetFromCenter * 18,
            y: 115,
            ease: "none",
            scrollTrigger: {
              trigger: pageRef.current,
              start: "top top",
              end: "+=700",
              scrub: true,
            },
          });
        });
      }

      // Single travelling Academic Signal motif across early sections, fading out cleanly
      if (motifRef.current) {
        gsap.to(motifRef.current, {
          x: -140,
          y: 185,
          rotate: -3,
          scale: 0.94,
          opacity: 0,
          ease: "none",
          scrollTrigger: {
            trigger: pageRef.current,
            start: "top top",
            end: "+=850",
            scrub: true,
          },
        });
      }

      // Play-once editorial section reveals
      gsap.utils.toArray<HTMLElement>(".editorial-reveal").forEach((el) => {
        gsap.from(el, {
          y: 18,
          opacity: 0,
          duration: 0.6,
          ease: "power2.out",
          clearProps: "transform,opacity",
          scrollTrigger: {
            trigger: el,
            start: "top 86%",
            once: true,
          },
        });
      });
    }, pageRef);

    return () => ctx.revert();
  }, [reducedMotion]);

  return (
    <div ref={pageRef} className="relative pt-[58px]">
      {/* Travelling Academic Signal cut-out (disabled on narrow viewports & reduced-motion) */}
      {!reducedMotion && (
        <div
          ref={motifRef}
          aria-hidden="true"
          className="pointer-events-none fixed right-8 top-28 z-10 hidden w-56 rounded-none border border-[var(--hairline)] bg-[#efe9dd] p-3 lg:block"
        >
          <p className="text-[10px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            Academic Signal · Sem-I
          </p>
          <svg viewBox="0 0 180 56" className="mt-2 h-12 w-full">
            <polyline
              fill="none"
              stroke="#2c4a8f"
              strokeWidth="1.8"
              points="4,46 38,38 72,42 108,24 142,20 176,10"
            />
            <circle
              cx="176"
              cy="10"
              r="2.8"
              fill="#efe9dd"
              stroke="#2c4a8f"
              strokeWidth="1.5"
            />
          </svg>
          <p className="mt-1 text-[10px] text-[#767e8c]">
            CIE + Attendance → Estimated Outcome
          </p>
        </div>
      )}

      {/* 1. HERO */}
      <section className="relative flex min-h-[calc(100vh-58px)] flex-col justify-between overflow-hidden border-b border-[var(--hairline)] bg-[#e5ded0] px-4 pt-12 sm:px-8">
        <div className="mx-auto w-full max-w-6xl">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[#767e8c]">
            NIET B.Tech CSE (Data Science) · SDG 4 Quality Education · PBL Team A11
          </p>
          <h1 className="mt-5 max-w-4xl font-editorial text-4xl font-normal leading-[1.08] text-[#141c2b] sm:text-6xl">
            An academic instrument for{" "}
            <em className="italic text-[#2c4a8f]">early signal detection</em> and
            syllabus-grounded preparation.
          </h1>
          <p className="mt-6 max-w-2xl text-xs leading-7 text-[#4a5364] sm:text-sm sm:leading-8">
            Organize CIE, ESE, and practical scores on a configurable credit ledger, inspect
            uncertainty-aware ML estimates, and practice with Gemini 2.5 Flash syllabus
            assessments—built for Classes 9–12 and undergraduate engineering.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/register" className="editorial-btn editorial-btn-primary rounded-none">
              Open Student Workspace
            </Link>
            <Link to="/classroom-challenge" className="editorial-btn rounded-none">
              Classroom Challenge (QR Demo)
            </Link>
          </div>
        </div>

        <div className="mx-auto mt-12 w-full max-w-6xl">
          <div className="grid grid-cols-2 border-t border-[var(--hairline)] py-3 text-[11px] uppercase tracking-[0.12em] text-[#4a5364] sm:grid-cols-4">
            <span>NIET Sem-I · 19 Credits</span>
            <span>900-Mark Scale (Audit Excl.)</span>
            <span>MySQL 11-Table Schema</span>
            <span>Gemini 2.5 Flash + Sklearn</span>
          </div>
        </div>

        <span className="sr-only">Scholia Academic Intelligence Platform</span>
        <div
          ref={wordmarkRef}
          aria-hidden="true"
          className="mt-4 -mb-6 flex w-[104%] -ml-[2%] select-none justify-between font-editorial text-[16vw] font-medium leading-[0.8] tracking-[-0.04em] text-[#141c2b]/90"
        >
          {WORDMARK_LETTERS.map((ch, idx) => (
            <span key={idx} className="inline-block">
              {ch}
            </span>
          ))}
        </div>
      </section>

      {/* 2. ARGUMENT (2-column problem vs platform response) */}
      <section className="border-b border-[var(--hairline)] bg-[#efe9dd] px-4 py-20 sm:px-8">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-12">
          <div className="editorial-reveal lg:col-span-5">
            <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
              01 / The Argument
            </p>
            <h2 className="mt-3 font-editorial text-3xl font-normal leading-tight text-[#141c2b] sm:text-4xl">
              Marksheets record what happened; students need clarity on{" "}
              <em className="italic text-[#2c4a8f]">what to adjust next</em>.
            </h2>
            <p className="mt-4 text-xs leading-7 text-[#4a5364]">
              Conventional tracking sheets split internal marks, attendance, and syllabus
              modules across disconnected documents. Scholia unites them under explicit
              validation and responsible statistical bounds.
            </p>
          </div>

          <div className="editorial-reveal divide-y divide-[var(--hairline)] border-y border-[var(--hairline)] lg:col-span-7">
            {[
              {
                problem: "Delayed Awareness",
                response:
                  "Every CIE, PS, PE, and attendance entry validates obtained marks against max marks and updates subject-level coverage immediately.",
              },
              {
                problem: "Unverified Predictions",
                response:
                  "Estimates are withheld below 3 recorded assessments so descriptive analytics are never replaced with invented numbers.",
              },
              {
                problem: "Course-Total Blindness",
                response:
                  "Topic-level proficiency comes strictly from unit quiz attempts and syllabus structure—never inferred from subject totals alone.",
              },
              {
                problem: "Classroom Friction",
                response:
                  "A direct mobile-ready /classroom-challenge route lets classmates scan a QR code and attempt NIET Sem-I units without account setup.",
              },
            ].map((row) => (
              <div key={row.problem} className="grid gap-2 py-5 sm:grid-cols-12">
                <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#141c2b] sm:col-span-4">
                  {row.problem}
                </span>
                <p className="text-xs leading-7 text-[#4a5364] sm:col-span-8">
                  {row.response}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. DEMONSTRATION (Self-drawing SVG Academic Signal) */}
      <section className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-20 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
                02 / Academic Signal Demonstration
              </p>
              <h2 className="mt-2 font-editorial text-3xl font-normal text-[#141c2b]">
                Self-drawing performance &amp; attendance traces
              </h2>
            </div>
            <p className="max-w-md text-xs leading-6 text-[#4a5364]">
              Toggle between CIE-to-ESE trajectory, attendance coupling, and unit-level
              concept profiles inside a fixed editorial frame.
            </p>
          </div>

          <AcademicSignalSvg />
        </div>
      </section>

      {/* 4. MODULES SHOWCASE (CardSwap + Ruled Module Rows) */}
      <section className="border-b border-[var(--hairline)] bg-[#efe9dd] px-4 py-20 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10">
            <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
              03 / Modules &amp; Materials
            </p>
            <h2 className="mt-2 font-editorial text-3xl font-normal text-[#141c2b]">
              Four integrated academic instruments
            </h2>
          </div>

          <div className="grid gap-10 lg:grid-cols-12 lg:items-start">
            <div className="lg:col-span-6">
              <CardSwap
                cards={MODULE_CARDS}
                onSelectCard={(c) => navigate(c.route)}
              />
            </div>

            <div className="divide-y divide-[var(--hairline)] border-y border-[var(--hairline)] lg:col-span-6">
              {MODULE_CARDS.map((mod) => (
                <div key={mod.code} className="py-4">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f]">
                      {mod.code} · {mod.category}
                    </span>
                    <Link
                      to={mod.route}
                      className="text-[11px] uppercase tracking-[0.1em] text-[#141c2b] underline underline-offset-4 hover:text-[#2c4a8f]"
                    >
                      Open
                    </Link>
                  </div>
                  <h3 className="mt-1 font-editorial text-xl text-[#141c2b]">{mod.title}</h3>
                  <p className="mt-1 text-xs leading-6 text-[#4a5364]">{mod.summary}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Preloaded NIET Sem-I table */}
          <div className="mt-14">
            <p className="text-[11px] uppercase tracking-[0.14em] text-[#767e8c]">
              Preloaded Curriculum — NIET B.Tech CSE (Data Science) · Semester-I (19 Credits · 900 Marks)
            </p>
            <div className="mt-4 overflow-x-auto border border-[var(--hairline)]">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-[var(--hairline)] bg-[#e5ded0] text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
                    <th className="px-4 py-3 font-normal">Code</th>
                    <th className="px-4 py-3 font-normal">Subject</th>
                    <th className="px-4 py-3 font-normal">Credits</th>
                    <th className="px-4 py-3 font-normal">Internal</th>
                    <th className="px-4 py-3 font-normal">External</th>
                    <th className="px-4 py-3 font-normal">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--hairline)]">
                  {[
                    ["CAS0103", "Calculus and Linear Algebra", "4", "CIE 50", "ESE 100", "150"],
                    ["CEC0101", "Digital Electronics and IoT Systems", "3", "CIE 50", "ESE 100", "150"],
                    ["CCSAI0101", "Fundamentals of Artificial Intelligence", "2", "CIE 50", "ESE 50", "100"],
                    ["CCSE0151", "C Programming", "2", "PS 50", "PE 50", "100"],
                    ["CCSE0152", "Web Designing", "1", "PS 25", "PE 25", "50"],
                    ["CMB0101", "Innovation and Entrepreneurship", "2", "CIE 100", "—", "100"],
                    ["CASL0101", "Foreign Language", "2", "CIE 50", "ESE 50", "100"],
                    ["CEC0151", "Digital Electronics Lab", "1", "PS 25", "PE 25", "50"],
                    ["CABC0151", "ABC Lab", "2", "PS 50", "PE 50", "100"],
                    ["CAU0101", "Compulsory Audit (Excluded from total)", "0", "Audit", "—", "Excluded"],
                  ].map((row) => (
                    <tr key={row[0]} className="hover:bg-[#e5ded0]/45">
                      <td className="px-4 py-3 font-bold text-[#2c4a8f]">{row[0]}</td>
                      <td className="px-4 py-3 text-[#141c2b]">{row[1]}</td>
                      <td className="px-4 py-3">{row[2]}</td>
                      <td className="px-4 py-3">{row[3]}</td>
                      <td className="px-4 py-3">{row[4]}</td>
                      <td className="px-4 py-3 font-bold">{row[5]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* 5. VERIFIED MEASUREMENTS (Zero fabricated numbers) */}
      <section className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-16 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            04 / Verified System Specifications
          </p>
          <h2 className="mt-2 font-editorial text-3xl font-normal text-[#141c2b]">
            Implemented architecture &amp; evidence boundaries
          </h2>
          <div className="mt-6 divide-y divide-[var(--hairline)] border-y border-[var(--hairline)]">
            {[
              ["Database Schema", "11 normalized MySQL tables managed via SQLAlchemy 2.0, PyMySQL, and Alembic"],
              ["Curriculum Preload", "10 NIET B.Tech CSE (Data Science) Semester-I courses totaling 19 credits and 900 marks (Compulsory Audit excluded)"],
              ["AI Question & Syllabus Pipeline", "Google Gemini API (google-genai SDK, gemini-2.5-flash) with reviewed local question-bank fallback"],
              ["ML Evaluation Protocol", "Ridge Regression & Random Forest Regressor compared against a Dummy mean baseline (MAE, RMSE, R²) with a >=3 assessment sufficiency gate"],
              ["Privacy & Ethics Guardrail", "Personal identifiers (names, emails, demo IDs) are excluded from LLM prompts and public aggregate classroom statistics"],
              ["Evaluation Status", "Platform prototype ready for classroom user testing; no unverified student adoption or live exam accuracy claims are made"],
            ].map(([k, v]) => (
              <div key={k} className="grid gap-2 py-4 sm:grid-cols-12">
                <span className="text-[11px] uppercase tracking-[0.1em] text-[#767e8c] sm:col-span-4">
                  {k}
                </span>
                <span className="text-xs leading-6 text-[#141c2b] sm:col-span-8">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. EDITORIAL CLOSE */}
      <footer className="overflow-hidden bg-[#efe9dd] px-4 pt-16 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-wrap items-center justify-between gap-6 border-b border-[var(--hairline)] pb-10">
            <div>
              <h2 className="font-editorial text-3xl font-normal text-[#141c2b]">
                Ready to inspect your semester signals?
              </h2>
              <p className="mt-2 max-w-xl text-xs leading-6 text-[#4a5364]">
                Limitations notice: ML predictions are statistical estimates with residual
                uncertainty intervals, not official university grades or guaranteed outcomes.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link to="/login" className="editorial-btn rounded-none">
                Try Demo Student
              </Link>
              <Link to="/classroom-challenge" className="editorial-btn editorial-btn-primary rounded-none">
                Launch Classroom Challenge
              </Link>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap justify-between gap-2 text-[11px] uppercase tracking-[0.1em] text-[#767e8c]">
            <span>Scholia · AI Academic Intelligence Platform</span>
            <span>PBL Team A11 · NIET B.Tech CSE (Data Science)</span>
          </div>
        </div>

        <div
          aria-hidden="true"
          className="mt-8 -mb-5 flex w-[104%] -ml-[2%] select-none justify-between font-editorial text-[14vw] font-medium leading-[0.8] tracking-[-0.04em] text-[#141c2b]/15"
        >
          {WORDMARK_LETTERS.map((ch, idx) => (
            <span key={idx}>{ch}</span>
          ))}
        </div>
      </footer>
    </div>
  );
}
