import { useEffect, useState } from "react";
import { apiRequest } from "../lib/api";

interface Subject {
  id: string;
  code: string;
  name: string;
  is_excluded_from_total: boolean;
}

interface FeatureContribution {
  feature: string;
  label: string;
  input_value: number;
  benchmark_mean: number;
  impact_points: number;
  direction: "positive" | "negative";
}

interface PredictionItem {
  id: string;
  subject_id: string | null;
  target_type: string;
  predicted_value: number | null;
  lower_bound: number | null;
  upper_bound: number | null;
  risk_signal: string | null;
  model_name: string;
  model_version: string;
  metrics_json: {
    held_out_mae?: number;
    assessments_used?: number;
    sufficiency_required?: number;
    assessments_found?: number;
    feature_contributions?: FeatureContribution[];
  } | null;
  explanation: string;
  is_available: boolean;
  created_at: string;
}

interface ModelMetricsJson {
  model_version: string;
  trained_at_utc: string;
  dataset_summary: {
    source: string;
    total_records: number;
    unique_students: number;
    split_protocol: string;
    train_records: number;
    validation_records: number;
    test_records: number;
  };
  selected_regressor: string;
  baseline_mean_mae: number;
  held_out_regression: { mae: number; rmse: number; r2: number };
  candidate_test_comparison: Record<string, { mae: number; rmse: number; r2: number }>;
  held_out_classification: {
    classifier_name: string;
    labels: string[];
    f1_weighted: number;
    f1_macro: number;
    precision_weighted: number;
    recall_weighted: number;
    confusion_matrix: number[][];
  };
  disclaimer: string;
}

export function PredictionsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [history, setHistory] = useState<PredictionItem[]>([]);
  const [modelCard, setModelCard] = useState<ModelMetricsJson | null>(null);
  const [running, setRunning] = useState(false);

  const loadData = async () => {
    const [subjs, hist, card] = await Promise.all([
      apiRequest<Subject[]>("/subjects"),
      apiRequest<PredictionItem[]>("/predictions/history"),
      apiRequest<ModelMetricsJson>("/predictions/model-card"),
    ]);
    setSubjects(subjs.filter((s) => !s.is_excluded_from_total));
    setHistory(hist);
    setModelCard(card);
  };

  useEffect(() => {
    void loadData();
  }, []);

  const runPrediction = async () => {
    setRunning(true);
    try {
      await apiRequest<PredictionItem>("/predictions", {
        method: "POST",
        body: JSON.stringify({
          subject_id: selectedSubjectId || null,
        }),
      });
      await loadData();
    } finally {
      setRunning(false);
    }
  };

  const latest = history[0];
  const contributions = latest?.metrics_json?.feature_contributions || [];

  return (
    <div className="space-y-8">
      <div className="border-b border-[var(--hairline)] pb-5">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
          ML Prediction Service · {modelCard?.model_version || "model_v1"}
        </p>
        <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
          Performance Estimates &amp; Evaluation Card
        </h1>
        <p className="mt-2 max-w-3xl text-xs leading-6 text-[#4a5364]">
          Benchmarked on public data; estimates are guidance, not official NIET grades.
          Subject or overall predictions require at least 2 recorded assessments; otherwise a
          descriptive fallback is shown.
        </p>
      </div>

      {/* Run panel */}
      <div className="flex flex-wrap items-end gap-4 border border-[var(--hairline)] bg-[#e5ded0] p-5">
        <div className="min-w-[260px] flex-1">
          <label htmlFor="pred-target" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
            Prediction Scope (Subject or Semester-I Overall)
          </label>
          <select
            id="pred-target"
            value={selectedSubjectId}
            onChange={(e) => setSelectedSubjectId(e.target.value)}
            className="mt-1 w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-2 text-xs"
          >
            <option value="">Semester-I Overall Percentage</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} — {s.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          disabled={running}
          onClick={() => void runPrediction()}
          className="editorial-btn editorial-btn-primary"
        >
          {running ? "Running Model..." : "Compute Estimate"}
        </button>
      </div>

      {/* Latest prediction result or descriptive fallback */}
      {latest && (
        <div className="border border-[var(--hairline)] bg-[#efe9dd] p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--hairline)] pb-3">
            <span className="text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f]">
              Latest Run · {latest.model_name} ({latest.model_version})
            </span>
            <span className="border border-[#141c2b] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em]">
              {latest.risk_signal?.replace(/_/g, " ")}
            </span>
          </div>

          {latest.is_available && latest.predicted_value !== null ? (
            <div className="grid gap-6 sm:grid-cols-3">
              <div>
                <span className="text-[10px] uppercase text-[#767e8c]">Point Estimate</span>
                <p className="mt-1 font-editorial text-5xl text-[#2c4a8f]">
                  {latest.predicted_value.toFixed(1)}%
                </p>
              </div>
              <div>
                <span className="text-[10px] uppercase text-[#767e8c]">
                  Next-Exam Range (Estimate ± MAE)
                </span>
                <p className="mt-1 font-editorial text-3xl text-[#141c2b]">
                  {latest.lower_bound?.toFixed(1)}% – {latest.upper_bound?.toFixed(1)}%
                </p>
                {latest.metrics_json?.held_out_mae !== undefined && (
                  <p className="mt-1 text-[11px] text-[#767e8c]">
                    ±{latest.metrics_json.held_out_mae.toFixed(2)} pts held-out MAE
                  </p>
                )}
              </div>
              <div>
                <span className="text-[10px] uppercase text-[#767e8c]">Support Signal</span>
                <p className="mt-1 font-editorial text-2xl text-[#141c2b]">{latest.risk_signal}</p>
                <p className="mt-1 text-[11px] text-[#4a5364]">
                  Support indicator only, not a fixed student label
                </p>
              </div>
            </div>
          ) : (
            <div>
              <p className="font-editorial text-2xl text-[#141c2b]">
                Prediction Withheld — Insufficient Assessment History (&lt; 2 Assessments)
              </p>
            </div>
          )}

          <p className="text-xs leading-6 text-[#4a5364]">{latest.explanation}</p>

          {/* Feature contributions */}
          {contributions.length > 0 && (
            <div className="border-t border-[var(--hairline)] pt-4">
              <p className="mb-3 text-[11px] uppercase tracking-[0.12em] text-[#2c4a8f]">
                Feature Contributions (Relative to Benchmark Mean)
              </p>
              <div className="divide-y divide-[var(--hairline)] border border-[var(--hairline)]">
                {contributions.map((c) => (
                  <div key={c.feature} className="grid gap-2 px-4 py-2.5 text-xs sm:grid-cols-12">
                    <span className="font-bold text-[#141c2b] sm:col-span-5">{c.label}</span>
                    <span className="text-[#4a5364] sm:col-span-4">
                      Input: {c.input_value} (benchmark mean {c.benchmark_mean})
                    </span>
                    <span
                      className={`font-bold sm:col-span-3 sm:text-right ${
                        c.impact_points >= 0 ? "text-[#2c4a8f]" : "text-[#141c2b]"
                      }`}
                    >
                      {c.impact_points >= 0 ? `+${c.impact_points}` : c.impact_points} pts
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Live Model Evaluation Card from model_metrics.json */}
      {modelCard && (
        <div className="border border-[var(--hairline)] bg-[#e5ded0]/60 p-6 space-y-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--hairline)] pb-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.12em] text-[#2c4a8f]">
                Live Evaluation Artifact — model_metrics.json ({modelCard.model_version})
              </p>
              <h2 className="mt-1 font-editorial text-2xl text-[#141c2b]">
                Held-Out Regression &amp; Risk Classification Metrics
              </h2>
            </div>
            <span className="text-[11px] text-[#767e8c]">
              Dummy Mean Baseline MAE: {modelCard.baseline_mean_mae}
            </span>
          </div>

          <p className="text-xs leading-6 text-[#4a5364]">
            {modelCard.dataset_summary.split_protocol} · {modelCard.dataset_summary.total_records}{" "}
            records across {modelCard.dataset_summary.unique_students} grouped students (
            {modelCard.dataset_summary.train_records} train /{" "}
            {modelCard.dataset_summary.validation_records} val /{" "}
            {modelCard.dataset_summary.test_records} test).
          </p>

          <div className="grid gap-4 sm:grid-cols-3">
            {Object.entries(modelCard.candidate_test_comparison).map(([name, m]) => (
              <div
                key={name}
                className={`border p-4 text-xs ${
                  name === modelCard.selected_regressor
                    ? "border-[#2c4a8f] bg-[#efe9dd]"
                    : "border-[var(--hairline)] bg-[#efe9dd]/60"
                }`}
              >
                <p className="font-bold uppercase tracking-[0.08em] text-[#141c2b]">
                  {name} {name === modelCard.selected_regressor ? "(Winner)" : ""}
                </p>
                <p className="mt-2 text-[#4a5364]">Held-Out MAE: {m.mae}</p>
                <p className="text-[#4a5364]">Held-Out RMSE: {m.rmse}</p>
                <p className="text-[#2c4a8f] font-bold">Held-Out R²: {m.r2}</p>
              </div>
            ))}

            <div className="border border-[var(--hairline)] bg-[#efe9dd] p-4 text-xs">
              <p className="font-bold uppercase tracking-[0.08em] text-[#141c2b]">
                {modelCard.held_out_classification.classifier_name} (Risk)
              </p>
              <p className="mt-2 text-[#2c4a8f] font-bold">
                Weighted F1: {modelCard.held_out_classification.f1_weighted}
              </p>
              <p className="text-[#4a5364]">
                Macro F1: {modelCard.held_out_classification.f1_macro}
              </p>
              <p className="text-[#4a5364]">
                Precision: {modelCard.held_out_classification.precision_weighted} · Recall:{" "}
                {modelCard.held_out_classification.recall_weighted}
              </p>
            </div>
          </div>

          <p className="border-t border-[var(--hairline)] pt-3 text-[11px] text-[#767e8c]">
            Benchmarked on public data; estimates are guidance, not official NIET grades.
          </p>
        </div>
      )}

      {/* History */}
      <div className="border border-[var(--hairline)]">
        <div className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-3 text-[11px] uppercase tracking-[0.1em]">
          Prediction History ({history.length})
        </div>
        <div className="divide-y divide-[var(--hairline)]">
          {history.length === 0 ? (
            <p className="p-4 text-xs text-[#767e8c]">No prediction runs recorded yet.</p>
          ) : (
            history.map((item) => (
              <div key={item.id} className="p-4 text-xs">
                <div className="flex flex-wrap justify-between gap-2">
                  <span className="font-bold text-[#141c2b]">
                    {item.target_type} ·{" "}
                    {item.is_available && item.predicted_value !== null
                      ? `${item.predicted_value.toFixed(1)}% (${item.lower_bound?.toFixed(1)}–${item.upper_bound?.toFixed(1)}%) · ${item.risk_signal}`
                      : "Withheld (< 2 assessments)"}
                  </span>
                  <span className="text-[11px] text-[#767e8c]">{item.model_version}</span>
                </div>
                <p className="mt-1 text-[#4a5364]">{item.explanation}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
