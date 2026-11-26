import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatedStepper, type StepDefinition } from "../components/ui/AnimatedStepper";
import { apiRequest } from "../lib/api";

interface ChallengeSubject {
  id: string;
  code: string;
  name: string;
  credits: number;
  total_max_marks: number;
  question_count: number;
  units: { id: string; title: string; order_index: number }[];
}

interface ChallengeConfig {
  institution: string;
  programme: string;
  academic_period: string;
  recommended_length: number;
  privacy_notice: string;
  subjects: ChallengeSubject[];
}

interface QuestionItem {
  id: string;
  question_text: string;
  difficulty: string;
  options: string[] | null;
}

interface TopicBreakdownItem {
  topic: string;
  correct: number;
  total: number;
  percentage: number;
  status: "Strength" | "Needs Review";
}

interface AttemptResponse {
  id: string;
  subject_code: string;
  subject_name: string;
  status: string;
  total_questions: number;
  score: number | null;
  max_score: number;
  questions: QuestionItem[];
  feedback: {
    question_id: string;
    question_text: string;
    difficulty: string;
    topic_title: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
  }[];
  difficulty_breakdown: Record<string, { correct: number; total: number }>;
  topic_breakdown: TopicBreakdownItem[];
}

export function ClassroomChallengePage() {
  const { attemptId } = useParams<{ attemptId?: string }>();
  const navigate = useNavigate();

  const [config, setConfig] = useState<ChallengeConfig | null>(null);
  const [participantName, setParticipantName] = useState("");
  const [demoCode, setDemoCode] = useState("");
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [attempt, setAttempt] = useState<AttemptResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentQIdx, setCurrentQIdx] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<ChallengeConfig>("/classroom-challenge/config")
      .then((cfg) => {
        setConfig(cfg);
        if (cfg.subjects.length > 0) setSelectedSubjectId(cfg.subjects[0].id);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load config"));
  }, []);

  useEffect(() => {
    if (!attemptId) {
      setAttempt(null);
      return;
    }
    apiRequest<AttemptResponse>(`/classroom-challenge/attempts/${attemptId}`)
      .then((a) => {
        setAttempt(a);
        setCurrentQIdx(0);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Attempt not found"));
  }, [attemptId]);

  const activeSubject = config?.subjects.find((s) => s.id === selectedSubjectId);

  const startAttempt = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiRequest<AttemptResponse>("/classroom-challenge/attempts", {
        method: "POST",
        body: JSON.stringify({
          subject_id: selectedSubjectId,
          unit_id: selectedUnitId || null,
          num_questions: config?.recommended_length || 10,
          mode: "classroom_challenge",
          participant_name: participantName.trim(),
          demo_identifier: demoCode.trim() || null,
        }),
      });
      setAttempt(created);
      setAnswers({});
      setCurrentQIdx(0);
      navigate(`/classroom-challenge/attempt/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start challenge");
    } finally {
      setSubmitting(false);
    }
  };

  const submitAttempt = async () => {
    if (!attempt) return;
    setSubmitting(true);
    setError(null);
    try {
      const scored = await apiRequest<AttemptResponse>(
        `/classroom-challenge/attempts/${attempt.id}/submit`,
        {
          method: "POST",
          body: JSON.stringify({
            answers: attempt.questions.map((q) => ({
              question_id: q.id,
              answer: answers[q.id] || "",
            })),
          }),
        }
      );
      setAttempt(scored);
      navigate(`/classroom-challenge/result/${scored.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  // Active 10-question quiz view (mobile-first single-column, static progress, zero scroll motion)
  if (attempt && attempt.status === "in_progress") {
    const q = attempt.questions[currentQIdx];
    const answeredCount = Object.keys(answers).length;
    const progressPct = ((currentQIdx + 1) / attempt.questions.length) * 100;

    return (
      <main className="mx-auto max-w-xl px-4 pt-20 pb-14">
        <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5 sm:p-7 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--hairline)] pb-3 text-[11px] uppercase tracking-[0.1em]">
            <span className="font-bold text-[#2c4a8f]">
              {attempt.subject_code} · {attempt.subject_name}
            </span>
            <span>
              Question {currentQIdx + 1} of {attempt.questions.length}
            </span>
          </div>

          {/* Static 1px question progress indicator */}
          <div
            role="progressbar"
            aria-valuemin={1}
            aria-valuemax={attempt.questions.length}
            aria-valuenow={currentQIdx + 1}
            className="h-[1px] w-full bg-[var(--hairline)]"
          >
            <div className="h-full bg-[#2c4a8f]" style={{ width: `${progressPct}%` }} />
          </div>

          {q && (
            <div className="space-y-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
                Difficulty: {q.difficulty}
              </p>
              <h1 className="font-editorial text-2xl font-normal leading-snug text-[#141c2b]">
                {q.question_text}
              </h1>
              <div className="space-y-2.5">
                {(q.options || []).map((opt) => (
                  <label
                    key={opt}
                    className={`flex items-start gap-3 border p-3.5 text-xs leading-5 cursor-pointer ${
                      answers[q.id] === opt
                        ? "border-[#2c4a8f] bg-[#e5ded0] font-bold"
                        : "border-[var(--hairline)] hover:border-[#141c2b]"
                    }`}
                  >
                    <input
                      type="radio"
                      name={`cc-${q.id}`}
                      checked={answers[q.id] === opt}
                      onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                      className="mt-0.5"
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--hairline)] pt-5">
            <button
              type="button"
              disabled={currentQIdx === 0}
              onClick={() => setCurrentQIdx((i) => Math.max(0, i - 1))}
              className="editorial-btn"
            >
              Previous
            </button>
            <span className="text-[11px] text-[#767e8c]">
              {answeredCount}/{attempt.questions.length} answered
            </span>
            {currentQIdx < attempt.questions.length - 1 ? (
              <button
                type="button"
                onClick={() => setCurrentQIdx((i) => i + 1)}
                className="editorial-btn editorial-btn-primary"
              >
                Next Question
              </button>
            ) : (
              <button
                type="button"
                disabled={submitting}
                onClick={() => void submitAttempt()}
                className="editorial-btn editorial-btn-primary"
              >
                {submitting ? "Scoring..." : "Submit Challenge"}
              </button>
            )}
          </div>
        </div>
      </main>
    );
  }

  // Scored Result view (instant score + topic strength/weakness breakdown + explanations)
  if (attempt && attempt.status === "submitted") {
    const pct =
      attempt.max_score > 0 && attempt.score !== null
        ? ((attempt.score / attempt.max_score) * 100).toFixed(1)
        : "0.0";
    return (
      <main className="mx-auto max-w-2xl px-4 pt-20 pb-16 space-y-6">
        <div className="border border-[var(--hairline)] bg-[#e5ded0] p-6">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            Classroom Challenge Result · {attempt.subject_code}
          </p>
          <h1 className="mt-2 font-editorial text-4xl text-[#141c2b]">
            {attempt.score} / {attempt.max_score} ({pct}%)
          </h1>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            {Object.entries(attempt.difficulty_breakdown).map(([diff, counts]) => (
              <span key={diff} className="border border-[var(--hairline)] bg-[#efe9dd] px-3 py-1">
                {diff}: {counts.correct}/{counts.total}
              </span>
            ))}
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                setAttempt(null);
                navigate("/classroom-challenge");
              }}
              className="editorial-btn"
            >
              Attempt Another Subject
            </button>
            <Link to="/classroom-challenge/projector" className="editorial-btn">
              Projector Stats View
            </Link>
          </div>
        </div>

        {/* Topic-wise Strength & Weakness Breakdown */}
        {attempt.topic_breakdown && attempt.topic_breakdown.length > 0 && (
          <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5 space-y-3">
            <h2 className="font-editorial text-2xl text-[#141c2b]">
              Topic-Wise Strength &amp; Weakness Breakdown
            </h2>
            <div className="divide-y divide-[var(--hairline)] border border-[var(--hairline)]">
              {attempt.topic_breakdown.map((t) => (
                <div key={t.topic} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs">
                  <span className="font-bold text-[#141c2b]">{t.topic}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-[#4a5364]">
                      {t.correct}/{t.total} ({t.percentage}%)
                    </span>
                    <span
                      className={`border px-2 py-0.5 text-[10px] uppercase ${
                        t.status === "Strength"
                          ? "border-[#2c4a8f] text-[#2c4a8f] font-bold"
                          : "border-[#141c2b] text-[#141c2b]"
                      }`}
                    >
                      {t.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Per-question explanations */}
        <div className="divide-y divide-[var(--hairline)] border border-[var(--hairline)] bg-[#efe9dd]">
          {attempt.feedback.map((f, idx) => (
            <div key={f.question_id} className="p-5 text-xs">
              <div className="flex flex-wrap justify-between gap-2 text-[10px] uppercase text-[#767e8c]">
                <span>{f.topic_title}</span>
                <span>{f.is_correct ? "Correct" : "Incorrect"}</span>
              </div>
              <p className="mt-1 font-bold text-[#141c2b]">
                {idx + 1}. {f.question_text}
              </p>
              <p className="mt-1.5 text-[#4a5364]">
                Your answer: <strong>{f.user_answer || "Not answered"}</strong> · Correct:{" "}
                <strong className="text-[#2c4a8f]">{f.correct_answer}</strong>
              </p>
              <p className="mt-1.5 text-[#767e8c]">{f.explanation}</p>
            </div>
          ))}
        </div>
      </main>
    );
  }

  // Mobile-first 3-step AnimatedStepper setup (no login required)
  const setupSteps: StepDefinition[] = [
    {
      id: "identify",
      title: "Display Name & Demo Code",
      subtitle:
        config?.privacy_notice ||
        "Enter a display name and optional demo code. Real ERP IDs are never required.",
      validate: () =>
        !participantName.trim() ? "Please enter a display name to continue." : null,
      content: (
        <div className="space-y-4">
          <div>
            <label htmlFor="cc-name" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Display Name (Required)
            </label>
            <input
              id="cc-name"
              value={participantName}
              onChange={(e) => setParticipantName(e.target.value)}
              placeholder="e.g. Ananya"
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2.5 text-xs"
            />
          </div>
          <div>
            <label htmlFor="cc-demo-code" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Optional Demo Code (Never enter a real ERP ID)
            </label>
            <input
              id="cc-demo-code"
              value={demoCode}
              onChange={(e) => setDemoCode(e.target.value)}
              placeholder="Optional, e.g. DEMO-A11"
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2.5 text-xs"
            />
          </div>
        </div>
      ),
    },
    {
      id: "subject",
      title: "Select NIET Sem-1 Subject & Unit",
      subtitle: "Choose any preloaded B.Tech CSE (Data Science) Semester-I subject.",
      validate: () => (!selectedSubjectId ? "Please select a subject." : null),
      content: (
        <div className="space-y-4">
          <div>
            <label htmlFor="cc-subj" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              NIET Sem-1 Subject
            </label>
            <select
              id="cc-subj"
              value={selectedSubjectId}
              onChange={(e) => {
                setSelectedSubjectId(e.target.value);
                setSelectedUnitId("");
              }}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2.5 text-xs"
            >
              {(config?.subjects || []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.code} — {s.name} ({s.question_count} Qs)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="cc-unit" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Module / Unit Focus (Optional)
            </label>
            <select
              id="cc-unit"
              value={selectedUnitId}
              onChange={(e) => setSelectedUnitId(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2.5 text-xs"
            >
              <option value="">All Subject Modules (10-Question Challenge)</option>
              {(activeSubject?.units || []).map((u) => (
                <option key={u.id} value={u.id}>
                  {u.order_index}. {u.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      ),
    },
    {
      id: "instructions",
      title: "Instructions & Start Quiz",
      subtitle: "Review the challenge format before starting.",
      content: (
        <ul className="space-y-2 border border-[var(--hairline)] bg-[#e5ded0]/40 p-4 text-xs leading-6 text-[#4a5364]">
          <li>• Programme: NIET B.Tech CSE (Data Science) · Semester-I</li>
          <li>• Subject: {activeSubject?.code} — {activeSubject?.name}</li>
          <li>• Length: {Math.min(10, activeSubject?.question_count || 10)} syllabus-grounded MCQs</li>
          <li>• Feedback: Instant score, explanations, and topic-wise Strength / Needs Review report</li>
          <li>• Privacy: Only anonymized aggregate scores appear on the classroom projector</li>
        </ul>
      ),
    },
  ];

  return (
    <main className="mx-auto max-w-xl px-4 pt-20 pb-16 space-y-6">
      <div className="border border-[var(--hairline)] bg-[#e5ded0] p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            Classroom Challenge · Direct QR Access
          </p>
          <Link
            to="/classroom-challenge/projector"
            className="text-[11px] uppercase tracking-[0.1em] text-[#2c4a8f] underline underline-offset-4"
          >
            Projector QR View →
          </Link>
        </div>
        <h1 className="mt-2 font-editorial text-3xl font-normal text-[#141c2b]">
          NIET CSE (DS) Sem-1 Proficiency Quiz
        </h1>
        <p className="mt-2 text-xs leading-6 text-[#4a5364]">
          No login required. Complete the 3-step setup below to attempt 10 verified
          first-semester questions.
        </p>
      </div>

      {error && (
        <p role="alert" className="border-l-2 border-[#141c2b] bg-[#e5ded0] p-3 text-xs">
          {error}
        </p>
      )}

      {config && (
        <AnimatedStepper
          steps={setupSteps}
          completeLabel="Start Quiz"
          onComplete={startAttempt}
          submitting={submitting}
        />
      )}
    </main>
  );
}
