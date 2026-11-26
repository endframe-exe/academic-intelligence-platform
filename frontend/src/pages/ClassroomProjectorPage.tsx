import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { apiRequest } from "../lib/api";

interface ProjectorStats {
  total_participants: number;
  total_submitted_attempts: number;
  average_percentage: number | null;
  hardest_topic: {
    topic: string;
    accuracy_percentage: number;
    responses: number;
  } | null;
  subject_participation: {
    code: string;
    name: string;
    attempts: number;
    average_percentage: number;
  }[];
}

export function ClassroomProjectorPage() {
  const [stats, setStats] = useState<ProjectorStats | null>(null);

  const challengeUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/classroom-challenge`
      : "/classroom-challenge";

  useEffect(() => {
    const fetchStats = () => {
      apiRequest<ProjectorStats>("/classroom-challenge/stats")
        .then(setStats)
        .catch(() => undefined);
    };
    fetchStats();
    const timer = window.setInterval(fetchStats, 5000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 pt-22 pb-16 space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            Classroom Presentation Projector · Live Anonymous Telemetry
          </p>
          <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
            Scan to Join NIET Sem-1 Challenge
          </h1>
          <p className="mt-2 text-xs text-[#4a5364]">
            Strictly anonymous aggregate metrics only—participant names and demo/ERP
            identifiers are never displayed on this screen.
          </p>
        </div>
        <Link to="/classroom-challenge" className="editorial-btn">
          Open Participant View
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-12 lg:items-start">
        {/* Large scannable QR card */}
        <div className="flex flex-col items-center border border-[var(--hairline)] bg-[#e5ded0] p-8 lg:col-span-5">
          <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5">
            <QRCodeSVG
              value={challengeUrl}
              size={228}
              bgColor="#efe9dd"
              fgColor="#141c2b"
              level="M"
            />
          </div>
          <p className="mt-4 text-[11px] font-bold uppercase tracking-[0.12em] text-[#2c4a8f]">
            Scan With Phone Camera
          </p>
          <p className="mt-1 break-all text-center text-[11px] text-[#4a5364]">
            {challengeUrl}
          </p>
        </div>

        {/* Anonymous live aggregate stats */}
        <div className="space-y-6 lg:col-span-7">
          <div className="grid grid-cols-1 border border-[var(--hairline)] bg-[#efe9dd] sm:grid-cols-3">
            <div className="p-5">
              <p className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
                Total Participants
              </p>
              <p className="mt-2 font-editorial text-5xl text-[#141c2b]">
                {stats?.total_participants ?? 0}
              </p>
              <p className="mt-1 text-[11px] text-[#4a5364]">Submitted attempts</p>
            </div>

            <div className="border-t border-[var(--hairline)] p-5 sm:border-t-0 sm:border-l">
              <p className="text-[10px] uppercase tracking-[0.12em] text-[#2c4a8f]">
                Average Class Score
              </p>
              <p className="mt-2 font-editorial text-5xl text-[#2c4a8f]">
                {stats?.average_percentage !== null && stats?.average_percentage !== undefined
                  ? `${stats.average_percentage.toFixed(1)}%`
                  : "—"}
              </p>
              <p className="mt-1 text-[11px] text-[#4a5364]">Across all Sem-1 subjects</p>
            </div>

            <div className="border-t border-[var(--hairline)] p-5 sm:border-t-0 sm:border-l">
              <p className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
                Hardest Topic
              </p>
              <p className="mt-2 font-editorial text-xl text-[#141c2b]">
                {stats?.hardest_topic ? stats.hardest_topic.topic : "Awaiting responses"}
              </p>
              <p className="mt-1 text-[11px] text-[#4a5364]">
                {stats?.hardest_topic
                  ? `${stats.hardest_topic.accuracy_percentage}% accuracy (${stats.hardest_topic.responses} Qs)`
                  : "Updates every 5 seconds"}
              </p>
            </div>
          </div>

          <div className="border border-[var(--hairline)] bg-[#efe9dd]">
            <div className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-3 text-[11px] uppercase tracking-[0.1em]">
              Anonymous Subject Participation Summary
            </div>
            <div className="divide-y divide-[var(--hairline)]">
              {stats && stats.subject_participation.length > 0 ? (
                stats.subject_participation.map((s) => (
                  <div
                    key={s.code}
                    className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs"
                  >
                    <span>
                      <strong className="text-[#2c4a8f]">{s.code}</strong> — {s.name}
                    </span>
                    <span className="text-[#4a5364]">
                      {s.attempts} attempt(s) · Mean {s.average_percentage}%
                    </span>
                  </div>
                ))
              ) : (
                <p className="p-4 text-xs text-[#767e8c]">
                  No completed attempts yet. Scan the QR code to submit the first attempt.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
