import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatedStepper, type StepDefinition } from "../components/ui/AnimatedStepper";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

export function OnboardingPage() {
  const { profile, refreshProfile } = useAuth();
  const navigate = useNavigate();

  const [educationLevel, setEducationLevel] = useState(
    profile?.education_level || "undergraduate"
  );
  const [institution, setInstitution] = useState(
    profile?.institution || "Noida Institute of Engineering and Technology (NIET)"
  );
  const [programme, setProgramme] = useState(
    profile?.programme || "B.Tech CSE (Data Science)"
  );
  const [academicPeriod, setAcademicPeriod] = useState(
    profile?.academic_period || "Semester-I"
  );
  const [gradingScheme, setGradingScheme] = useState(
    profile?.grading_scheme || "NIET 900-Mark Credit System"
  );
  const [weeklyHours, setWeeklyHours] = useState(
    String(profile?.weekly_study_hours ?? 14)
  );
  const [saving, setSaving] = useState(false);

  const handleComplete = async () => {
    setSaving(true);
    try {
      await apiRequest("/students/me", {
        method: "PATCH",
        body: JSON.stringify({
          education_level: educationLevel,
          institution,
          programme,
          academic_period: academicPeriod,
          grading_scheme: gradingScheme,
          weekly_study_hours: Number(weeklyHours) || 14,
        }),
      });
      await refreshProfile();
      navigate("/dashboard");
    } finally {
      setSaving(false);
    }
  };

  const steps: StepDefinition[] = [
    {
      id: "level",
      title: "Education Level",
      subtitle: "Select your academic stage so subject rules and grading scales adapt accordingly.",
      validate: () => (!educationLevel ? "Please select an education level." : null),
      content: (
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { id: "undergraduate", label: "Undergraduate (B.Tech / B.Sc)" },
            { id: "class_11_12", label: "Senior Secondary (Class 11–12)" },
            { id: "class_9_10", label: "Secondary (Class 9–10)" },
          ].map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => setEducationLevel(opt.id)}
              className={`border p-4 text-left text-xs transition-colors cursor-pointer ${
                educationLevel === opt.id
                  ? "border-[#2c4a8f] bg-[#e5ded0] text-[#141c2b] font-bold"
                  : "border-[var(--hairline)] text-[#4a5364] hover:border-[#141c2b]"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      ),
    },
    {
      id: "programme",
      title: "Institution & Programme",
      subtitle: "Specify your institution and degree/board configuration.",
      validate: () =>
        !institution.trim() || !programme.trim()
          ? "Institution and programme are required."
          : null,
      content: (
        <div className="space-y-4">
          <div>
            <label htmlFor="onb-inst" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Institution / Board
            </label>
            <input
              id="onb-inst"
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
          <div>
            <label htmlFor="onb-prog" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Programme / Stream
            </label>
            <input
              id="onb-prog"
              value={programme}
              onChange={(e) => setProgramme(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
        </div>
      ),
    },
    {
      id: "period",
      title: "Semester & Grading Scale",
      subtitle: "Confirm your current academic term and weekly study availability.",
      validate: () =>
        !academicPeriod.trim() || !gradingScheme.trim()
          ? "Academic period and grading scheme are required."
          : null,
      content: (
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="onb-period" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Academic Period
            </label>
            <input
              id="onb-period"
              value={academicPeriod}
              onChange={(e) => setAcademicPeriod(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
          <div>
            <label htmlFor="onb-scheme" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Grading Scheme
            </label>
            <input
              id="onb-scheme"
              value={gradingScheme}
              onChange={(e) => setGradingScheme(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
          <div>
            <label htmlFor="onb-hours" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Weekly Study Hours Target
            </label>
            <input
              id="onb-hours"
              type="number"
              min={1}
              max={80}
              value={weeklyHours}
              onChange={(e) => setWeeklyHours(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
        </div>
      ),
    },
    {
      id: "review",
      title: "Review Configuration",
      subtitle: "Verify your academic profile before entering the workspace.",
      content: (
        <dl className="divide-y divide-[var(--hairline)] border border-[var(--hairline)] bg-[#e5ded0]/40 text-xs">
          {[
            ["Education Level", educationLevel],
            ["Institution", institution],
            ["Programme", programme],
            ["Academic Period", academicPeriod],
            ["Grading Scheme", gradingScheme],
            ["Weekly Study Hours", `${weeklyHours} hrs/week`],
          ].map(([k, v]) => (
            <div key={k} className="grid grid-cols-3 px-4 py-3">
              <dt className="text-[11px] uppercase tracking-[0.08em] text-[#767e8c]">{k}</dt>
              <dd className="col-span-2 font-bold text-[#141c2b]">{v}</dd>
            </div>
          ))}
        </dl>
      ),
    },
  ];

  return (
    <main className="mx-auto max-w-3xl px-4 pt-24 pb-24">
      <p className="mb-2 text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
        Guided Academic Onboarding
      </p>
      <AnimatedStepper
        steps={steps}
        completeLabel="Save & Open Dashboard"
        onComplete={handleComplete}
        submitting={saving}
      />
    </main>
  );
}
