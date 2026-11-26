import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiRequest } from "../lib/api";
import { useAuth } from "../context/AuthContext";

interface SubjectSummary {
  subject_id: string;
  code: string;
  name: string;
  credits: number;
  category: string;
  is_excluded_from_total: boolean;
  total_max_marks: number;
  obtained_marks: number;
  recorded_max_marks: number;
  percentage: number | null;
  attendance_percentage: number | null;
  assessments_count: number;
}

interface DashboardData {
  overall_percentage: number | null;
  total_credits: number;
  total_credit_marks_scale: number;
  recorded_marks_total: number;
  recorded_max_total: number;
  attendance_overall_percentage: number | null;
  assessments_count: number;
  subjects: SubjectSummary[];
  trend: { label: string; subject_code: string; date: string; percentage: number }[];
  strengths: string[];
  improvement_areas: string[];
  data_coverage_note: string;
}

interface PredictionItem {
  id: string;
  target_type: string;
  predicted_value: number | null;
  lower_bound: number | null;
  upper_bound: number | null;
  risk_signal: string | null;
  model_name: string;
  model_version: string;
  is_available: boolean;
}

export function DashboardPage() {
  const { profile } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [latestEstimate, setLatestEstimate] = useState<PredictionItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiRequest<DashboardData>("/analytics/dashboard"),
      apiRequest<PredictionItem[]>("/predictions/history").catch(() => []),
    ])
      .then(([dash, preds]) => {
        setData(dash);
        const overall = preds.find((p) => p.target_type === "overall_percentage") || preds[0] || null;
        setLatestEstimate(overall);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load dashboard"));
  }, []);

  if (error) {
    return <p className="border-l-2 border-[#141c2b] bg-[#e5ded0] p-4 text-xs">{error}</p>;
  }
  if (!data) {
    return <p className="text-xs uppercase tracking-[0.1em] text-[#767e8c]">Loading analytics...</p>;
  }

  const chartSubjects = data.subjects
    .filter((s) => !s.is_excluded_from_total)
    .map((s) => ({
      code: s.code,
      actualMarksPct: s.percentage ?? 0,
      actualAttendancePct: s.attendance_percentage ?? 0,
    }));

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--hairline)] pb-6">
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            Academic Overview · {profile?.programme || "B.Tech CSE (Data Science)"} ·{" "}
            {profile?.academic_period || "Semester-I"}
          </p>
          <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
            Performance Ledger
          </h1>
          <p className="mt-2 text-xs text-[#4a5364]">{data.data_coverage_note}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/academics" className="editorial-btn">
            Add / Import Marks
          </Link>
          <Link to="/predictions" className="editorial-btn editorial-btn-primary">
            Run Prediction
          </Link>
        </div>
      </div>

      {/* Actual vs Estimated summary strip */}
      <div className="grid grid-cols-2 border border-[var(--hairline)] bg-[#e5ded0] sm:grid-cols-4">
        <div className="p-5">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
            ACTUAL Recorded Average
          </p>
          <p className="mt-2 font-editorial text-3xl text-[#141c2b]">
            {data.overall_percentage !== null ? `${data.overall_percentage.toFixed(1)}%` : "No marks"}
          </p>
          <p className="mt-1 text-[11px] text-[#4a5364]">
            {data.recorded_marks_total} / {data.recorded_max_total} actual marks
          </p>
        </div>

        <div className="border-l border-[var(--hairline)] p-5">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#2c4a8f]">
            ESTIMATED Semester Outcome
          </p>
          <p className="mt-2 font-editorial text-3xl text-[#2c4a8f]">
            {latestEstimate?.is_available && latestEstimate.predicted_value !== null
              ? `${latestEstimate.predicted_value.toFixed(1)}%`
              : "Not run / <3"}
          </p>
          <p className="mt-1 text-[11px] text-[#4a5364]">
            {latestEstimate?.is_available && latestEstimate.lower_bound !== null
              ? `90% interval: ${latestEstimate.lower_bound.toFixed(1)}–${latestEstimate.upper_bound?.toFixed(1)}%`
              : data.assessments_count >= 2
                ? "Run estimate in Predictions"
                : "Requires >=2 assessments"}
          </p>
        </div>

        <div className="border-t border-[var(--hairline)] p-5 sm:border-t-0 sm:border-l">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
            ACTUAL Attendance
          </p>
          <p className="mt-2 font-editorial text-3xl text-[#141c2b]">
            {data.attendance_overall_percentage !== null
              ? `${data.attendance_overall_percentage.toFixed(1)}%`
              : "Not logged"}
          </p>
          <p className="mt-1 text-[11px] text-[#4a5364]">Threshold target: 75%</p>
        </div>

        <div className="border-t border-l border-[var(--hairline)] p-5 sm:border-t-0">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#767e8c]">
            Curriculum Scale
          </p>
          <p className="mt-2 font-editorial text-3xl text-[#141c2b]">
            {data.total_credit_marks_scale} Marks
          </p>
          <p className="mt-1 text-[11px] text-[#4a5364]">{data.total_credits} Credits</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f]">
            Subject-Wise Actual Marks % vs. Actual Attendance %
          </p>
          <div className="mt-4 h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartSubjects} margin={{ top: 10, right: 12, left: -12, bottom: 20 }}>
                <CartesianGrid stroke="rgba(20,28,43,0.12)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="code"
                  tick={{ fontSize: 10, fill: "#4a5364", fontFamily: "Courier Prime" }}
                  angle={-25}
                  textAnchor="end"
                />
                <YAxis
                  domain={[0, 100]}
                  unit="%"
                  tick={{ fontSize: 10, fill: "#4a5364", fontFamily: "Courier Prime" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#efe9dd",
                    border: "1px solid rgba(20,28,43,0.25)",
                    fontSize: "11px",
                    fontFamily: "Courier Prime",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "10px", fontFamily: "Courier Prime" }} />
                <Bar dataKey="actualMarksPct" name="Actual Marks %" fill="#141c2b" />
                <Bar
                  dataKey="actualAttendancePct"
                  name="Actual Attendance %"
                  fill="#efe9dd"
                  stroke="#2c4a8f"
                  strokeWidth={1.5}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f]">
            Chronological Trend (Actual Scores vs. Estimated Benchmark %)
          </p>
          <div className="mt-4 h-64 w-full">
            {data.trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.trend} margin={{ top: 10, right: 12, left: -12, bottom: 20 }}>
                  <CartesianGrid stroke="rgba(20,28,43,0.12)" strokeDasharray="3 3" />
                  <XAxis
                    dataKey="subject_code"
                    tick={{ fontSize: 10, fill: "#4a5364", fontFamily: "Courier Prime" }}
                  />
                  <YAxis
                    domain={[0, 100]}
                    unit="%"
                    tick={{ fontSize: 10, fill: "#4a5364", fontFamily: "Courier Prime" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#efe9dd",
                      border: "1px solid rgba(20,28,43,0.25)",
                      fontSize: "11px",
                      fontFamily: "Courier Prime",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "10px", fontFamily: "Courier Prime" }} />
                  {latestEstimate?.is_available && latestEstimate.predicted_value !== null && (
                    <ReferenceLine
                      y={latestEstimate.predicted_value}
                      stroke="#2c4a8f"
                      strokeDasharray="4 4"
                      label={{
                        value: `Est. ${latestEstimate.predicted_value.toFixed(1)}%`,
                        position: "insideTopRight",
                        fill: "#2c4a8f",
                        fontSize: 10,
                      }}
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="percentage"
                    name="Actual Score %"
                    stroke="#2c4a8f"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#efe9dd", stroke: "#2c4a8f", strokeWidth: 1.5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center border border-dashed border-[var(--hairline)] text-xs text-[#767e8c]">
                Log your first CIE or Practical score to plot trends.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Strengths & Improvement Areas */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="border border-[var(--hairline)] bg-[#e5ded0]/60 p-5">
          <h2 className="font-editorial text-xl text-[#141c2b]">Observed Strengths</h2>
          <ul className="mt-3 space-y-2 text-xs text-[#4a5364]">
            {data.strengths.length > 0 ? (
              data.strengths.map((s) => <li key={s}>+ {s}</li>)
            ) : (
              <li>No subjects above 70% recorded yet.</li>
            )}
          </ul>
        </div>
        <div className="border border-[var(--hairline)] bg-[#e5ded0]/60 p-5">
          <h2 className="font-editorial text-xl text-[#141c2b]">Areas Needing Attention</h2>
          <ul className="mt-3 space-y-2 text-xs text-[#4a5364]">
            {data.improvement_areas.length > 0 ? (
              data.improvement_areas.map((s) => <li key={s}>! {s}</li>)
            ) : (
              <li>No recorded subjects below 75% right now.</li>
            )}
          </ul>
        </div>
      </div>

      {/* Subject ledger table */}
      <div className="overflow-x-auto border border-[var(--hairline)]">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-[var(--hairline)] bg-[#e5ded0] text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              <th className="px-4 py-3 font-normal">Code</th>
              <th className="px-4 py-3 font-normal">Subject</th>
              <th className="px-4 py-3 font-normal">Cr</th>
              <th className="px-4 py-3 font-normal">Max Scale</th>
              <th className="px-4 py-3 font-normal">Actual Marks</th>
              <th className="px-4 py-3 font-normal">Actual Avg</th>
              <th className="px-4 py-3 font-normal">Actual Attendance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--hairline)]">
            {data.subjects.map((s) => (
              <tr key={s.subject_id} className="hover:bg-[#e5ded0]/40">
                <td className="px-4 py-3 font-bold text-[#2c4a8f]">{s.code}</td>
                <td className="px-4 py-3">
                  {s.name}
                  {s.is_excluded_from_total && (
                    <span className="ml-2 border border-[var(--hairline)] px-1.5 py-0.5 text-[10px] text-[#767e8c]">
                      Excluded from 900 total
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">{s.credits}</td>
                <td className="px-4 py-3">{s.is_excluded_from_total ? "Audit" : s.total_max_marks}</td>
                <td className="px-4 py-3">
                  {s.recorded_max_marks > 0
                    ? `${s.obtained_marks} / ${s.recorded_max_marks}`
                    : "—"}
                </td>
                <td className="px-4 py-3 font-bold">
                  {s.percentage !== null ? `${s.percentage.toFixed(1)}%` : "—"}
                </td>
                <td className="px-4 py-3">
                  {s.attendance_percentage !== null
                    ? `${s.attendance_percentage.toFixed(1)}%`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
