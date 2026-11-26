import React, { useEffect, useState } from "react";
import { API_BASE, apiRequest, getStoredToken } from "../lib/api";

interface Subject {
  id: string;
  code: string;
  name: string;
  internal_label: string;
  internal_max_marks: number;
}

interface AcademicRecord {
  id: string;
  subject_code: string;
  subject_name: string;
  title: string;
  assessment_type: string;
  marks_obtained: number;
  max_marks: number;
  percentage: number;
  assessment_date: string | null;
}

interface Attendance {
  id: string;
  subject_code: string;
  subject_name: string;
  classes_attended: number;
  total_classes: number;
  percentage: number;
  recorded_date: string;
}

interface CsvPreviewRow {
  row_number: number;
  subject_code: string;
  title: string;
  assessment_type: string;
  marks_obtained: number;
  max_marks: number;
  assessment_date: string | null;
  study_hours_logged: number | null;
  valid: boolean;
  error: string | null;
}

interface CsvPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: CsvPreviewRow[];
}

export function RecordsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [records, setRecords] = useState<AcademicRecord[]>([]);
  const [attendance, setAttendance] = useState<Attendance[]>([]);

  // Marks form
  const [subjectId, setSubjectId] = useState("");
  const [title, setTitle] = useState("");
  const [assessmentType, setAssessmentType] = useState("CIE");
  const [maxMarks, setMaxMarks] = useState("50");
  const [marksObtained, setMarksObtained] = useState("");
  const [assessmentDate, setAssessmentDate] = useState("2026-11-15");
  const [studyHours, setStudyHours] = useState("4");

  // Inline edit state for marks & attendance
  const [editingMarkId, setEditingMarkId] = useState<string | null>(null);
  const [editingMarkVal, setEditingMarkVal] = useState("");
  const [editingAttId, setEditingAttId] = useState<string | null>(null);
  const [editingAttObt, setEditingAttObt] = useState("");
  const [editingAttTot, setEditingAttTot] = useState("");

  // Attendance form
  const [attSubjectId, setAttSubjectId] = useState("");
  const [attended, setAttended] = useState("");
  const [totalClasses, setTotalClasses] = useState("");
  const [attDate, setAttDate] = useState("2026-11-20");

  // CSV preview
  const [csvPreview, setCsvPreview] = useState<CsvPreviewResponse | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAll = async () => {
    const [subjs, recs, att] = await Promise.all([
      apiRequest<Subject[]>("/subjects"),
      apiRequest<AcademicRecord[]>("/records"),
      apiRequest<Attendance[]>("/attendance"),
    ]);
    setSubjects(subjs);
    setRecords(recs);
    setAttendance(att);
    if (subjs.length > 0 && !subjectId) {
      setSubjectId(subjs[0].id);
      setAttSubjectId(subjs[0].id);
    }
  };

  useEffect(() => {
    void loadAll();
  }, []);

  const submitMark = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    const obtNum = Number(marksObtained);
    const maxNum = Number(maxMarks);
    if (Number.isNaN(obtNum) || Number.isNaN(maxNum) || maxNum <= 0 || obtNum < 0) {
      setError("Marks must be non-negative and max marks must be greater than 0.");
      return;
    }
    if (obtNum > maxNum) {
      setError(`Validation error: obtained marks (${obtNum}) cannot exceed max marks (${maxNum}).`);
      return;
    }

    try {
      await apiRequest("/records", {
        method: "POST",
        body: JSON.stringify({
          subject_id: subjectId,
          title,
          assessment_type: assessmentType,
          max_marks: maxNum,
          marks_obtained: obtNum,
          assessment_date: assessmentDate || null,
          study_hours_logged: studyHours ? Number(studyHours) : null,
        }),
      });
      setTitle("");
      setMarksObtained("");
      setMessage("Assessment mark recorded.");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save record");
    }
  };

  const saveEditMark = async (rec: AcademicRecord) => {
    setError(null);
    const nextVal = Number(editingMarkVal);
    if (Number.isNaN(nextVal) || nextVal < 0 || nextVal > rec.max_marks) {
      setError(`Updated marks must be between 0 and ${rec.max_marks}.`);
      return;
    }
    await apiRequest(`/records/${rec.id}`, {
      method: "PATCH",
      body: JSON.stringify({ marks_obtained: nextVal }),
    });
    setEditingMarkId(null);
    setMessage("Assessment mark updated.");
    await loadAll();
  };

  const deleteMark = async (id: string) => {
    await apiRequest(`/records/${id}`, { method: "DELETE" });
    await loadAll();
  };

  const submitAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    const attNum = Number(attended);
    const totNum = Number(totalClasses);
    if (totNum <= 0 || attNum < 0 || attNum > totNum) {
      setError(`Validation error: classes attended (${attNum}) cannot exceed total classes (${totNum}).`);
      return;
    }

    try {
      await apiRequest("/attendance", {
        method: "POST",
        body: JSON.stringify({
          subject_id: attSubjectId,
          classes_attended: attNum,
          total_classes: totNum,
          recorded_date: attDate,
        }),
      });
      setAttended("");
      setTotalClasses("");
      setMessage("Attendance record saved.");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save attendance");
    }
  };

  const saveEditAttendance = async (id: string) => {
    setError(null);
    const nextAtt = Number(editingAttObt);
    const nextTot = Number(editingAttTot);
    if (nextTot <= 0 || nextAtt < 0 || nextAtt > nextTot) {
      setError("Updated classes attended cannot exceed total classes.");
      return;
    }
    await apiRequest(`/attendance/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ classes_attended: nextAtt, total_classes: nextTot }),
    });
    setEditingAttId(null);
    setMessage("Attendance record updated.");
    await loadAll();
  };

  const deleteAttendance = async (id: string) => {
    await apiRequest(`/attendance/${id}`, { method: "DELETE" });
    await loadAll();
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setMessage(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const preview = await apiRequest<CsvPreviewResponse>("/imports/preview", {
        method: "POST",
        body: form,
      });
      setCsvPreview(preview);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV preview failed");
    }
  };

  const confirmCsv = async () => {
    if (!csvPreview) return;
    setError(null);
    try {
      const res = await apiRequest<{ imported_count: number }>("/imports/confirm", {
        method: "POST",
        body: JSON.stringify({ rows: csvPreview.rows }),
      });
      setMessage(`Imported ${res.imported_count} validated row(s).`);
      setCsvPreview(null);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import confirmation failed");
    }
  };

  const downloadTemplate = async () => {
    const res = await fetch(`${API_BASE}/imports/template`, {
      headers: { Authorization: `Bearer ${getStoredToken()}` },
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "academic_records_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      <div className="border-b border-[var(--hairline)] pb-5">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
          Academic Data Management
        </p>
        <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
          Marks, Attendance &amp; CSV Import
        </h1>
      </div>

      {message && (
        <p className="border-l-2 border-[#2c4a8f] bg-[#e5ded0] px-4 py-2 text-xs text-[#141c2b]">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="border-l-2 border-[#141c2b] bg-[#e5ded0] px-4 py-2 text-xs text-[#141c2b]">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Manual Marks Entry */}
        <form onSubmit={submitMark} className="border border-[var(--hairline)] bg-[#efe9dd] p-5 space-y-4">
          <h2 className="font-editorial text-2xl text-[#141c2b]">Log Examination / Internal Marks</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label htmlFor="rec-subj" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Subject
              </label>
              <select
                id="rec-subj"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              >
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.code} — {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="rec-title" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Assessment Title
              </label>
              <input
                id="rec-title"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="CIE-1 Unit Test"
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label htmlFor="rec-type" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Type
              </label>
              <select
                id="rec-type"
                value={assessmentType}
                onChange={(e) => setAssessmentType(e.target.value)}
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              >
                {["CIE", "ESE", "PS", "PE", "QUIZ", "ASSIGNMENT", "INTERNAL", "AUDIT"].map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="rec-obt" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Marks Obtained
              </label>
              <input
                id="rec-obt"
                type="number"
                step="0.5"
                min={0}
                required
                value={marksObtained}
                onChange={(e) => setMarksObtained(e.target.value)}
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label htmlFor="rec-max" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Max Marks
              </label>
              <input
                id="rec-max"
                type="number"
                step="0.5"
                min={1}
                required
                value={maxMarks}
                onChange={(e) => setMaxMarks(e.target.value)}
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label htmlFor="rec-date" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Date
              </label>
              <input
                id="rec-date"
                type="date"
                value={assessmentDate}
                onChange={(e) => setAssessmentDate(e.target.value)}
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label htmlFor="rec-hrs" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                Study Hours Logged
              </label>
              <input
                id="rec-hrs"
                type="number"
                step="0.5"
                min={0}
                value={studyHours}
                onChange={(e) => setStudyHours(e.target.value)}
                className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
              />
            </div>
          </div>
          <button type="submit" className="editorial-btn editorial-btn-primary">
            Save Assessment Score
          </button>
        </form>

        {/* Attendance + CSV Import */}
        <div className="space-y-6">
          <form onSubmit={submitAttendance} className="border border-[var(--hairline)] bg-[#efe9dd] p-5 space-y-4">
            <h2 className="font-editorial text-2xl text-[#141c2b]">Log Subject Attendance</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label htmlFor="att-subj" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Subject
                </label>
                <select
                  id="att-subj"
                  value={attSubjectId}
                  onChange={(e) => setAttSubjectId(e.target.value)}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
                >
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.code} — {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="att-count" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Classes Attended
                </label>
                <input
                  id="att-count"
                  type="number"
                  min={0}
                  required
                  value={attended}
                  onChange={(e) => setAttended(e.target.value)}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
                />
              </div>
              <div>
                <label htmlFor="att-tot" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Total Classes Held
                </label>
                <input
                  id="att-tot"
                  type="number"
                  min={1}
                  required
                  value={totalClasses}
                  onChange={(e) => setTotalClasses(e.target.value)}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
                />
              </div>
              <div className="sm:col-span-2">
                <label htmlFor="att-date" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Recorded Date
                </label>
                <input
                  id="att-date"
                  type="date"
                  required
                  value={attDate}
                  onChange={(e) => setAttDate(e.target.value)}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/60 px-3 py-2 text-xs"
                />
              </div>
            </div>
            <button type="submit" className="editorial-btn">
              Save Attendance
            </button>
          </form>

          <div className="border border-[var(--hairline)] bg-[#e5ded0]/60 p-5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-editorial text-xl text-[#141c2b]">CSV Import &amp; Preview</h2>
              <button
                type="button"
                onClick={downloadTemplate}
                className="text-[11px] uppercase tracking-[0.1em] text-[#2c4a8f] underline cursor-pointer"
              >
                Download Template
              </button>
            </div>
            <input
              type="file"
              accept=".csv"
              aria-label="Upload CSV marks file"
              onChange={handleCsvUpload}
              className="block w-full border border-[var(--hairline)] bg-[#efe9dd] p-2 text-xs"
            />
          </div>
        </div>
      </div>

      {csvPreview && (
        <div className="border border-[var(--hairline)] bg-[#efe9dd] p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs">
              Previewing {csvPreview.total_rows} rows:{" "}
              <strong className="text-[#2c4a8f]">{csvPreview.valid_rows} valid</strong>,{" "}
              <strong>{csvPreview.invalid_rows} invalid</strong>.
            </p>
            <button
              type="button"
              disabled={csvPreview.valid_rows === 0}
              onClick={confirmCsv}
              className="editorial-btn editorial-btn-primary"
            >
              Confirm Valid Rows ({csvPreview.valid_rows})
            </button>
          </div>
          <div className="overflow-x-auto border border-[var(--hairline)]">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#e5ded0] text-[10px] uppercase">
                <tr>
                  <th className="px-3 py-2">Row</th>
                  <th className="px-3 py-2">Code</th>
                  <th className="px-3 py-2">Title</th>
                  <th className="px-3 py-2">Marks</th>
                  <th className="px-3 py-2">Validation Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--hairline)]">
                {csvPreview.rows.map((r) => (
                  <tr key={r.row_number}>
                    <td className="px-3 py-2">{r.row_number}</td>
                    <td className="px-3 py-2">{r.subject_code}</td>
                    <td className="px-3 py-2">{r.title}</td>
                    <td className="px-3 py-2">
                      {r.marks_obtained}/{r.max_marks}
                    </td>
                    <td className={`px-3 py-2 ${r.valid ? "text-[#2c4a8f]" : "font-bold text-[#141c2b]"}`}>
                      {r.valid ? "Valid" : `Error: ${r.error}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Existing Records & Attendance tables with full Edit + Delete */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="border border-[var(--hairline)]">
          <div className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-3 text-[11px] uppercase tracking-[0.1em]">
            Recorded Assessments ({records.length})
          </div>
          <div className="divide-y divide-[var(--hairline)]">
            {records.length === 0 ? (
              <p className="p-4 text-xs text-[#767e8c]">No marks recorded yet.</p>
            ) : (
              records.map((r) => (
                <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs">
                  <div>
                    <p className="font-bold text-[#141c2b]">
                      {r.subject_code} · {r.title} ({r.assessment_type})
                    </p>
                    {editingMarkId === r.id ? (
                      <div className="mt-1.5 flex items-center gap-2">
                        <input
                          type="number"
                          step="0.5"
                          min={0}
                          max={r.max_marks}
                          aria-label={`Edit marks for ${r.title}`}
                          value={editingMarkVal}
                          onChange={(e) => setEditingMarkVal(e.target.value)}
                          className="w-20 border border-[#2c4a8f] bg-[#e5ded0] px-2 py-1 text-xs"
                        />
                        <span>/ {r.max_marks}</span>
                        <button
                          type="button"
                          onClick={() => void saveEditMark(r)}
                          className="text-[11px] uppercase text-[#2c4a8f] underline cursor-pointer"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingMarkId(null)}
                          className="text-[11px] uppercase text-[#767e8c] cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <p className="text-[11px] text-[#4a5364]">
                        {r.marks_obtained} / {r.max_marks} ({r.percentage.toFixed(1)}%)
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {editingMarkId !== r.id && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingMarkId(r.id);
                          setEditingMarkVal(String(r.marks_obtained));
                        }}
                        className="text-[11px] uppercase text-[#2c4a8f] hover:underline cursor-pointer"
                      >
                        Edit
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => void deleteMark(r.id)}
                      className="text-[11px] uppercase text-[#767e8c] hover:text-[#141c2b] cursor-pointer"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="border border-[var(--hairline)]">
          <div className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-3 text-[11px] uppercase tracking-[0.1em]">
            Attendance Log ({attendance.length})
          </div>
          <div className="divide-y divide-[var(--hairline)]">
            {attendance.length === 0 ? (
              <p className="p-4 text-xs text-[#767e8c]">No attendance logged yet.</p>
            ) : (
              attendance.map((a) => (
                <div key={a.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs">
                  <div>
                    <p className="font-bold text-[#141c2b]">
                      {a.subject_code} — {a.subject_name}
                    </p>
                    {editingAttId === a.id ? (
                      <div className="mt-1.5 flex items-center gap-2">
                        <input
                          type="number"
                          min={0}
                          aria-label="Edit classes attended"
                          value={editingAttObt}
                          onChange={(e) => setEditingAttObt(e.target.value)}
                          className="w-16 border border-[#2c4a8f] bg-[#e5ded0] px-2 py-1 text-xs"
                        />
                        <span>/</span>
                        <input
                          type="number"
                          min={1}
                          aria-label="Edit total classes"
                          value={editingAttTot}
                          onChange={(e) => setEditingAttTot(e.target.value)}
                          className="w-16 border border-[#2c4a8f] bg-[#e5ded0] px-2 py-1 text-xs"
                        />
                        <button
                          type="button"
                          onClick={() => void saveEditAttendance(a.id)}
                          className="text-[11px] uppercase text-[#2c4a8f] underline cursor-pointer"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingAttId(null)}
                          className="text-[11px] uppercase text-[#767e8c] cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <p className="text-[11px] text-[#4a5364]">
                        {a.classes_attended} / {a.total_classes} classes ({a.recorded_date})
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-[#2c4a8f]">{a.percentage.toFixed(1)}%</span>
                    {editingAttId !== a.id && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingAttId(a.id);
                          setEditingAttObt(String(a.classes_attended));
                          setEditingAttTot(String(a.total_classes));
                        }}
                        className="text-[11px] uppercase text-[#2c4a8f] hover:underline cursor-pointer"
                      >
                        Edit
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => void deleteAttendance(a.id)}
                      className="text-[11px] uppercase text-[#767e8c] hover:text-[#141c2b] cursor-pointer"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
