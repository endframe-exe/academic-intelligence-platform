import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { usePrefersReducedMotion } from "../lib/utils";

gsap.registerPlugin(ScrollTrigger);

interface SignalVariant {
  id: string;
  label: string;
  path: string;
  endPoint: { x: number; y: number };
  facts: [string, string, string];
}

const VARIANTS: SignalVariant[] = [
  {
    id: "trajectory",
    label: "CIE → ESE Trajectory",
    path: "M 20 155 C 90 142, 145 102, 220 96 C 295 90, 355 58, 460 36",
    endPoint: { x: 460, y: 36 },
    facts: [
      "Input signal: CIE & Practical Sessional marks",
      "Validation gate: >= 3 recorded assessments required",
      "Output framing: Estimated range with residual uncertainty",
    ],
  },
  {
    id: "attendance",
    label: "Attendance Coupling",
    path: "M 20 148 L 110 132 L 200 108 L 290 88 L 375 68 L 460 44",
    endPoint: { x: 460, y: 44 },
    facts: [
      "Threshold flag: < 75% attendance triggers support notice",
      "Feature role: Combined with weekly study hours",
      "Fallback mode: Descriptive summary shown if attendance missing",
    ],
  },
  {
    id: "mastery",
    label: "Unit Concept Profile",
    path: "M 20 130 Q 110 40, 200 112 T 370 72 T 460 38",
    endPoint: { x: 460, y: 38 },
    facts: [
      "Granularity: Topic & unit feedback from quiz attempts",
      "Rule boundary: Never inferred from subject totals alone",
      "Grounding: NIET Sem-I syllabus & Gemini-parsed modules",
    ],
  },
];

export function AcademicSignalSvg() {
  const [selectedId, setSelectedId] = useState(VARIANTS[0].id);
  const containerRef = useRef<HTMLDivElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  const hasScrolledInRef = useRef(false);
  const reducedMotion = usePrefersReducedMotion();

  const active = VARIANTS.find((v) => v.id === selectedId) || VARIANTS[0];

  useEffect(() => {
    const pathEl = pathRef.current;
    if (!pathEl) return;

    if (reducedMotion) {
      pathEl.style.strokeDasharray = "none";
      pathEl.style.strokeDashoffset = "0";
      return;
    }

    const length = pathEl.getTotalLength();
    pathEl.style.strokeDasharray = `${length}`;
    pathEl.style.strokeDashoffset = `${length}`;

    const ctx = gsap.context(() => {
      if (hasScrolledInRef.current) {
        gsap.to(pathEl, {
          strokeDashoffset: 0,
          duration: 1.8,
          ease: "power2.out",
        });
      } else {
        gsap.to(pathEl, {
          strokeDashoffset: 0,
          duration: 2.0,
          ease: "power2.out",
          scrollTrigger: containerRef.current
            ? {
                trigger: containerRef.current,
                start: "top 82%",
                once: true,
                onEnter: () => {
                  hasScrolledInRef.current = true;
                },
              }
            : undefined,
        });
      }
    }, containerRef);

    return () => ctx.revert();
  }, [selectedId, reducedMotion]);

  return (
    <div
      ref={containerRef}
      className="rounded-none border border-[var(--hairline)] bg-[#efe9dd] p-5 sm:p-7"
    >
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-[var(--hairline)] pb-4">
        <span className="text-[11px] uppercase tracking-[0.14em] text-[#767e8c]">
          Signal Demonstration — Self-Drawing Trace
        </span>
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Signal variants">
          {VARIANTS.map((v) => (
            <button
              key={v.id}
              type="button"
              role="tab"
              aria-selected={v.id === selectedId}
              onClick={() => {
                hasScrolledInRef.current = true;
                setSelectedId(v.id);
              }}
              className={`rounded-none border px-2.5 py-1 text-[11px] uppercase tracking-[0.08em] transition-colors cursor-pointer ${
                v.id === selectedId
                  ? "border-[#2c4a8f] text-[#2c4a8f] font-bold"
                  : "border-[var(--hairline)] text-[#4a5364] hover:border-[#141c2b]"
              }`}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <svg
        viewBox="0 0 480 180"
        role="img"
        aria-label={`Academic signal graph illustrating ${active.label}`}
        className="h-48 w-full border border-[var(--hairline)] bg-[#e5ded0]/55"
      >
        <line x1="20" y1="40" x2="460" y2="40" stroke="rgba(20,28,43,0.12)" strokeDasharray="3 3" />
        <line x1="20" y1="90" x2="460" y2="90" stroke="rgba(20,28,43,0.12)" strokeDasharray="3 3" />
        <line x1="20" y1="140" x2="460" y2="140" stroke="rgba(20,28,43,0.12)" strokeDasharray="3 3" />
        <line x1="20" y1="160" x2="460" y2="160" stroke="rgba(20,28,43,0.35)" />
        <line x1="20" y1="20" x2="20" y2="160" stroke="rgba(20,28,43,0.35)" />

        <path
          ref={pathRef}
          d={active.path}
          fill="none"
          stroke="#2c4a8f"
          strokeWidth="2"
          strokeLinecap="square"
        />
        <circle
          cx={active.endPoint.x}
          cy={active.endPoint.y}
          r="3.5"
          fill="#efe9dd"
          stroke="#2c4a8f"
          strokeWidth="1.5"
        />
      </svg>

      <div className="mt-5 grid gap-3 border-t border-[var(--hairline)] pt-4 sm:grid-cols-3">
        {active.facts.map((fact, idx) => (
          <div key={idx} className="text-[11px] leading-6 text-[#4a5364]">
            <span className="mr-1.5 text-[#2c4a8f]">0{idx + 1}.</span>
            {fact}
          </div>
        ))}
      </div>
    </div>
  );
}
