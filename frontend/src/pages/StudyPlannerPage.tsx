import { useEffect, useState } from "react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../context/AuthContext";

interface Recommendation {
  id: string;
  subject_code: string | null;
  subject_name: string | null;
  priority: "high" | "medium" | "low";
  title: string;
  evidence: string;
  action: string;
  suggested_hours_per_week: number;
  source: string;
}

interface EditableSession {
  id: string;
  day: string;
  subject_code: string;
  subject_name: string;
  focus_topic: string;
  duration_hours: number;
  rationale: string;
  status: "planned" | "completed" | "dismissed";
}

interface StudyPlanApi {
  weekly_hours_available: number;
  exam_days_remaining: number;
  sessions: Omit<EditableSession, "id" | "status">[];
  ai_summary: string;
  ai_used: boolean;
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function StudyPlannerPage() {
  const { user } = useAuth();
  const storageKey = `scholia_study_sessions_${user?.id || "anon"}`;

  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [sessions, setSessions] = useState<EditableSession[]>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? (JSON.parse(saved) as EditableSession[]) : [];
    } catch {
      return [];
    }
  });
  const [aiSummary, setAiSummary] = useState<string>("");
  const [aiUsed, setAiUsed] = useState(false);
  const [weeklyHours, setWeeklyHours] = useState("14");
  const [daysRemaining, setDaysRemaining] = useState("21");
  const [generating, setGenerating] = useState(false);

  // Add custom session inputs
  const [newDay, setNewDay] = useState("Saturday");
  const [newCode, setNewCode] = useState("CAS0103");
  const [newTopic, setNewTopic] = useState("");
  const [newHours, setNewHours] = useState("2");

  useEffect(() => {
    apiRequest<Recommendation[]>("/recommendations").then(setRecs);
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(sessions));
    } catch {
      // ignore storage quota errors
    }
  }, [sessions, storageKey]);

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const res = await apiRequest<StudyPlanApi>("/study-plans", {
        method: "POST",
        body: JSON.stringify({
          weekly_hours_available: Number(weeklyHours) || 14,
          exam_days_remaining: Number(daysRemaining) || 21,
        }),
      });
      setAiSummary(res.ai_summary);
      setAiUsed(res.ai_used);
      setSessions(
        res.sessions.map((s, idx) => ({
          ...s,
          id: `sess-${Date.now()}-${idx}`,
          status: "planned",
        }))
      );
    } finally {
      setGenerating(false);
    }
  };

  const updateSession = (id: string, patch: Partial<EditableSession>) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, ...patch } : s)));
  };

  const removeSession = (id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const addCustomSession = () => {
    if (!newTopic.trim()) return;
    setSessions((prev) => [
      ...prev,
      {
        id: `custom-${Date.now()}`,
        day: newDay,
        subject_code: newCode.trim().toUpperCase() || "STUDY",
        subject_name: "Custom Revision",
        focus_topic: newTopic.trim(),
        duration_hours: Math.max(0.5, Number(newHours) || 1.5),
        rationale: "Student-added revision block",
        status: "planned",
      },
    ]);
    setNewTopic("");
  };

  const totalPlannedHours = sessions
    .filter((s) => s.status !== "dismissed")
    .reduce((acc, s) => acc + Number(s.duration_hours || 0), 0);

  return (
    <div className="space-y-8">
      <div className="border-b border-[var(--hairline)] pb-5">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
          Hybrid Study Intelligence
        </p>
        <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
          Recommendations &amp; Editable Weekly Schedule
        </h1>
      </div>

      {/* Recommendations */}
      <div className="space-y-3">
        <h2 className="font-editorial text-2xl text-[#141c2b]">
          Rule-Based Priority Recommendations (With Evidence)
        </h2>
        <div className="divide-y divide-[var(--hairline)] border border-[var(--hairline)]">
          {recs.map((r) => (
            <div key={r.id} className="bg-[#efe9dd] p-4 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold text-[#141c2b]">{r.title}</span>
                <span className="border border-[var(--hairline)] px-2 py-0.5 text-[10px] uppercase text-[#2c4a8f]">
                  {r.priority} priority · {r.suggested_hours_per_week} hrs/wk
                </span>
              </div>
              <p className="mt-1.5 text-[#4a5364]">
                <strong>Evidence:</strong> {r.evidence}
              </p>
              <p className="mt-1 text-[#141c2b]">
                <strong>Recommended Action:</strong> {r.action}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Study Plan Generator */}
      <div className="border border-[var(--hairline)] bg-[#e5ded0] p-5 space-y-4">
        <h2 className="font-editorial text-2xl text-[#141c2b]">Generate Weekly Revision Schedule</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="sp-hrs" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Weekly Study Hours Available
            </label>
            <input
              id="sp-hrs"
              type="number"
              min={1}
              max={80}
              value={weeklyHours}
              onChange={(e) => setWeeklyHours(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-2 text-xs"
            />
          </div>
          <div>
            <label htmlFor="sp-days" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Days Until Examinations
            </label>
            <input
              id="sp-days"
              type="number"
              min={1}
              max={365}
              value={daysRemaining}
              onChange={(e) => setDaysRemaining(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-2 text-xs"
            />
          </div>
          <div className="flex items-end">
            <button
              type="button"
              disabled={generating}
              onClick={() => void generatePlan()}
              className="editorial-btn editorial-btn-primary w-full"
            >
              {generating ? "Allocating..." : "Generate Schedule"}
            </button>
          </div>
        </div>
      </div>

      {/* Editable Weekly Sessions */}
      <div className="space-y-4 border border-[var(--hairline)] bg-[#efe9dd] p-5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--hairline)] pb-3">
          <div>
            <h3 className="font-editorial text-2xl text-[#141c2b]">
              Weekly Revision Sessions ({totalPlannedHours.toFixed(1)} active hrs)
            </h3>
            {aiSummary && (
              <p className="mt-1 text-xs leading-6 text-[#4a5364]">
                <span className="mr-2 uppercase text-[10px] text-[#2c4a8f]">
                  [{aiUsed ? "Gemini 2.5 Flash Summary" : "Rule Summary"}]
                </span>
                {aiSummary}
              </p>
            )}
          </div>
        </div>

        {sessions.length === 0 ? (
          <p className="text-xs text-[#767e8c]">
            Click "Generate Schedule" above or add a custom study session below.
          </p>
        ) : (
          <div className="divide-y divide-[var(--hairline)] border border-[var(--hairline)]">
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`grid gap-3 p-4 text-xs sm:grid-cols-12 sm:items-center ${
                  s.status === "dismissed" ? "opacity-50" : ""
                }`}
              >
                <div className="sm:col-span-2">
                  <select
                    aria-label="Session day"
                    value={s.day}
                    onChange={(e) => updateSession(s.id, { day: e.target.value })}
                    className="w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-2 py-1.5 text-xs font-bold text-[#2c4a8f]"
                  >
                    {DAYS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-4 space-y-1">
                  <span className="block text-[10px] uppercase text-[#767e8c]">
                    {s.subject_code} · {s.rationale}
                  </span>
                  <input
                    aria-label="Focus topic"
                    value={s.focus_topic}
                    onChange={(e) => updateSession(s.id, { focus_topic: e.target.value })}
                    className="w-full border border-[var(--hairline)] bg-[#e5ded0]/40 px-2 py-1 text-xs text-[#141c2b]"
                  />
                </div>
                <div className="flex items-center gap-1 sm:col-span-2">
                  <input
                    aria-label="Duration hours"
                    type="number"
                    step="0.5"
                    min={0.5}
                    max={12}
                    value={s.duration_hours}
                    onChange={(e) =>
                      updateSession(s.id, { duration_hours: Number(e.target.value) || 0.5 })
                    }
                    className="w-16 border border-[var(--hairline)] bg-[#e5ded0]/40 px-2 py-1 text-xs"
                  />
                  <span>hrs</span>
                </div>
                <div className="flex flex-wrap items-center gap-2 sm:col-span-4 sm:justify-end">
                  <button
                    type="button"
                    onClick={() =>
                      updateSession(s.id, {
                        status: s.status === "completed" ? "planned" : "completed",
                      })
                    }
                    className={`border px-2 py-1 text-[10px] uppercase cursor-pointer ${
                      s.status === "completed"
                        ? "border-[#2c4a8f] text-[#2c4a8f] font-bold"
                        : "border-[var(--hairline)] text-[#4a5364]"
                    }`}
                  >
                    {s.status === "completed" ? "Completed" : "Mark Done"}
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      updateSession(s.id, {
                        status: s.status === "dismissed" ? "planned" : "dismissed",
                      })
                    }
                    className="border border-[var(--hairline)] px-2 py-1 text-[10px] uppercase text-[#767e8c] cursor-pointer"
                  >
                    {s.status === "dismissed" ? "Restore" : "Dismiss"}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeSession(s.id)}
                    className="text-[10px] uppercase text-[#767e8c] hover:text-[#141c2b] cursor-pointer"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add custom session */}
        <div className="grid gap-3 border-t border-[var(--hairline)] pt-4 sm:grid-cols-12">
          <select
            aria-label="New session day"
            value={newDay}
            onChange={(e) => setNewDay(e.target.value)}
            className="border border-[var(--hairline)] bg-[#e5ded0]/50 px-2 py-2 text-xs sm:col-span-2"
          >
            {DAYS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <input
            aria-label="New session subject code"
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            placeholder="Code (e.g. CAS0103)"
            className="border border-[var(--hairline)] bg-[#e5ded0]/50 px-2 py-2 text-xs sm:col-span-2"
          />
          <input
            aria-label="New session focus topic"
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            placeholder="Custom topic (e.g. Eigenvalues practice)"
            className="border border-[var(--hairline)] bg-[#e5ded0]/50 px-2 py-2 text-xs sm:col-span-4"
          />
          <input
            aria-label="New session duration hours"
            type="number"
            step="0.5"
            min={0.5}
            value={newHours}
            onChange={(e) => setNewHours(e.target.value)}
            className="border border-[var(--hairline)] bg-[#e5ded0]/50 px-2 py-2 text-xs sm:col-span-2"
          />
          <button
            type="button"
            onClick={addCustomSession}
            className="editorial-btn sm:col-span-2"
          >
            Add Session
          </button>
        </div>
      </div>
    </div>
  );
}
