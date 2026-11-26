import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

export function ProfilePage() {
  const { user, profile, refreshProfile } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [institution, setInstitution] = useState(profile?.institution || "");
  const [programme, setProgramme] = useState(profile?.programme || "");
  const [period, setPeriod] = useState(profile?.academic_period || "");
  const [hours, setHours] = useState(String(profile?.weekly_study_hours ?? 14));
  const [saved, setSaved] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(null);
    await apiRequest("/students/me", {
      method: "PATCH",
      body: JSON.stringify({
        name,
        institution,
        programme,
        academic_period: period,
        weekly_study_hours: Number(hours) || 14,
      }),
    });
    await refreshProfile();
    setSaved("Academic profile updated.");
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div className="border-b border-[var(--hairline)] pb-5">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
          Settings &amp; Privacy
        </p>
        <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
          Student Profile &amp; Academic Config
        </h1>
      </div>

      <form onSubmit={handleSave} className="border border-[var(--hairline)] bg-[#efe9dd] p-6 space-y-4">
        <div>
          <label htmlFor="prof-name" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
            Student Name
          </label>
          <input
            id="prof-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
          />
        </div>
        <div>
          <label htmlFor="prof-inst" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
            Institution
          </label>
          <input
            id="prof-inst"
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="prof-prog" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Programme
            </label>
            <input
              id="prof-prog"
              value={programme}
              onChange={(e) => setProgramme(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
          <div>
            <label htmlFor="prof-period" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Academic Period
            </label>
            <input
              id="prof-period"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
        </div>
        <div>
          <label htmlFor="prof-hrs" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
            Weekly Study Hours
          </label>
          <input
            id="prof-hrs"
            type="number"
            min={1}
            max={80}
            value={hours}
            onChange={(e) => setHours(e.target.value)}
            className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
          />
        </div>

        {saved && <p className="text-xs text-[#2c4a8f]">{saved}</p>}

        <button type="submit" className="editorial-btn editorial-btn-primary">
          Save Configuration
        </button>
      </form>

      <div className="border border-[var(--hairline)] bg-[#e5ded0] p-5 text-xs leading-6 text-[#4a5364]">
        <p className="font-bold uppercase tracking-[0.1em] text-[#141c2b]">
          Data Privacy &amp; Responsible AI Policy
        </p>
        <p className="mt-2">
          Personal identifiers (name, email, demo IDs) are never forwarded to Gemini 2.5
          Flash or exposed in Classroom Challenge aggregate analytics. All predictions are
          advisory estimates accompanied by model version and uncertainty intervals.
        </p>
      </div>
    </div>
  );
}
