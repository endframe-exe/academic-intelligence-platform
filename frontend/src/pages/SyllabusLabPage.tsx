import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AnimatedStepper, type StepDefinition } from "../components/ui/AnimatedStepper";
import { apiRequest } from "../lib/api";

interface Subject {
  id: string;
  code: string;
  name: string;
  units_topics: { id: string; title: string; order_index: number }[];
}

interface EditableUnit {
  title: string;
  topics: string[];
}

interface SyllabusDoc {
  id: string;
  filename: string;
  file_type: string;
  processing_status: string;
  extracted_structure_json: {
    subject_name?: string;
    units?: EditableUnit[];
    chunks?: string[];
  } | null;
  created_at: string;
}

interface QuestionItem {
  id: string;
  question_text: string;
  difficulty: string;
  options: string[] | null;
  source: string;
}

interface QuizAttempt {
  id: string;
  status: string;
  score: number | null;
  max_score: number;
  questions: QuestionItem[];
  feedback: {
    question_id: string;
    question_text: string;
    topic_title: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
  }[];
  topic_breakdown: {
    topic: string;
    correct: number;
    total: number;
    percentage: number;
    status: string;
  }[];
}

type LabTab = "upload" | "library" | "assessments";

export function SyllabusLabPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const deriveTab = (): LabTab => {
    if (location.pathname.endsWith("/library")) return "library";
    if (location.pathname.endsWith("/assessments")) return "assessments";
    return "upload";
  };

  const [tab, setTab] = useState<LabTab>(deriveTab);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [docs, setDocs] = useState<SyllabusDoc[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [selectedDocId, setSelectedDocId] = useState("");
  const [numQuestions, setNumQuestions] = useState("5");
  const [difficulty, setDifficulty] = useState("mixed");

  // Upload & Review Stepper state
  const [file, setFile] = useState<File | null>(null);
  const [activeDoc, setActiveDoc] = useState<SyllabusDoc | null>(null);
  const [editableSubjectName, setEditableSubjectName] = useState("");
  const [editableUnits, setEditableUnits] = useState<EditableUnit[]>([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Quiz state
  const [quiz, setQuiz] = useState<QuizAttempt | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [genNotice, setGenNotice] = useState<string | null>(null);
  const [genSource, setGenSource] = useState<string | null>(null);

  useEffect(() => {
    setTab(deriveTab());
  }, [location.pathname]);

  const switchTab = (next: LabTab) => {
    setTab(next);
    navigate(`/syllabus-lab/${next}`);
  };

  const loadAll = async () => {
    const [subjs, docList] = await Promise.all([
      apiRequest<Subject[]>("/subjects"),
      apiRequest<SyllabusDoc[]>("/documents"),
    ]);
    setSubjects(subjs);
    setDocs(docList);
    if (subjs.length > 0 && !selectedSubjectId) {
      setSelectedSubjectId(subjs[0].id);
    }
  };

  useEffect(() => {
    void loadAll();
  }, []);

  const currentSubject = subjects.find((s) => s.id === selectedSubjectId);

  const handleUpload = async () => {
    if (!file) return;
    setError(null);
    setMessage(null);
    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds the 5 MB syllabus upload limit.");
      return;
    }
    setSaving(true);
    const form = new FormData();
    form.append("file", file);
    if (selectedSubjectId) form.append("subject_id", selectedSubjectId);
    try {
      const doc = await apiRequest<SyllabusDoc>("/documents", {
        method: "POST",
        body: form,
      });
      setActiveDoc(doc);
      setEditableSubjectName(
        doc.extracted_structure_json?.subject_name || currentSubject?.name || doc.filename
      );
      setEditableUnits(doc.extracted_structure_json?.units || []);
      setSelectedDocId(doc.id);
      setMessage(`Extracted text & ${(doc.extracted_structure_json?.chunks || []).length} chunk(s) from ${doc.filename}.`);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSaving(false);
    }
  };

  const confirmAndSaveChunks = async () => {
    if (!activeDoc) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await apiRequest<SyllabusDoc>(`/documents/${activeDoc.id}/review`, {
        method: "PATCH",
        body: JSON.stringify({
          subject_name: editableSubjectName,
          units: editableUnits,
        }),
      });
      setActiveDoc(updated);
      setSelectedDocId(updated.id);
      setMessage(
        `Confirmed & saved ${(updated.extracted_structure_json?.chunks || []).length} syllabus chunks to MySQL.`
      );
      await loadAll();
      switchTab("assessments");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save reviewed structure");
    } finally {
      setSaving(false);
    }
  };

  const generateAndStartQuiz = async () => {
    if (!selectedSubjectId) return;
    setSaving(true);
    setError(null);
    setGenNotice(null);
    setGenSource(null);
    try {
      const count = Math.min(10, Math.max(5, Number(numQuestions) || 5));
      const genRes = await apiRequest<{
        ai_used: boolean;
        source: string;
        notice: string;
        retrieved_chunks_count: number;
        questions: QuestionItem[];
      }>("/question-sets/generate", {
        method: "POST",
        body: JSON.stringify({
          subject_id: selectedSubjectId,
          unit_id: selectedUnitId || null,
          syllabus_document_id: selectedDocId || null,
          num_questions: count,
          difficulty,
        }),
      });
      setGenNotice(genRes.notice);
      setGenSource(genRes.source);

      if (genRes.questions.length === 0) {
        setError("No questions found for this subject/unit yet. Try selecting All Modules or uploading a syllabus.");
        return;
      }

      const attempt = await apiRequest<QuizAttempt>("/quiz-attempts", {
        method: "POST",
        body: JSON.stringify({
          subject_id: selectedSubjectId,
          unit_id: selectedUnitId || null,
          num_questions: genRes.questions.length,
          mode: "practice",
          question_ids: genRes.questions.map((q) => q.id),
        }),
      });
      setQuiz(attempt);
      setAnswers({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate quiz");
    } finally {
      setSaving(false);
    }
  };

  const submitQuiz = async () => {
    if (!quiz) return;
    const payload = {
      answers: quiz.questions.map((q) => ({
        question_id: q.id,
        answer: answers[q.id] || "",
      })),
    };
    const scored = await apiRequest<QuizAttempt>(`/quiz-attempts/${quiz.id}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setQuiz(scored);
  };

  const updateUnitTitle = (idx: number, title: string) => {
    setEditableUnits((prev) => prev.map((u, i) => (i === idx ? { ...u, title } : u)));
  };

  const updateUnitTopics = (idx: number, rawCsv: string) => {
    const topics = rawCsv
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    setEditableUnits((prev) => prev.map((u, i) => (i === idx ? { ...u, topics } : u)));
  };

  const addUnit = () => {
    setEditableUnits((prev) => [...prev, { title: "New Unit", topics: ["Topic 1"] }]);
  };

  const removeUnit = (idx: number) => {
    setEditableUnits((prev) => prev.filter((_, i) => i !== idx));
  };

  const stepperSteps: StepDefinition[] = [
    {
      id: "upload",
      title: "Upload File",
      subtitle: "Upload a PDF or DOCX syllabus (max 5 MB). Personal data is never sent to Gemini.",
      validate: () => {
        if (!activeDoc) return "Upload and extract a syllabus file before continuing.";
        return null;
      },
      content: (
        <div className="space-y-4">
          <div>
            <label htmlFor="sl-subj" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Link to Subject
            </label>
            <select
              id="sl-subj"
              value={selectedSubjectId}
              onChange={(e) => {
                setSelectedSubjectId(e.target.value);
                setSelectedUnitId("");
              }}
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
            <label htmlFor="sl-file" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Syllabus Document (PDF or DOCX, max 5 MB)
            </label>
            <input
              id="sl-file"
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="mt-1 block w-full border border-[var(--hairline)] bg-[#e5ded0]/40 p-2 text-xs"
            />
          </div>
          <button
            type="button"
            disabled={!file || saving}
            onClick={() => void handleUpload()}
            className="editorial-btn"
          >
            {saving ? "Extracting Text..." : "Upload & Extract Syllabus"}
          </button>
          {activeDoc && (
            <p className="text-xs text-[#2c4a8f]">
              Ready: <strong>{activeDoc.filename}</strong> ({activeDoc.processing_status})
            </p>
          )}
        </div>
      ),
    },
    {
      id: "review",
      title: "Extract & Edit Units",
      subtitle: "Review and refine the extracted subject title, units, and comma-separated topics.",
      validate: () =>
        editableUnits.length === 0 ? "Keep at least one unit before confirming." : null,
      content: (
        <div className="space-y-4">
          <div>
            <label htmlFor="sl-edit-subj" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
              Extracted Subject Name
            </label>
            <input
              id="sl-edit-subj"
              value={editableSubjectName}
              onChange={(e) => setEditableSubjectName(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs"
            />
          </div>
          <div className="space-y-3">
            {editableUnits.map((u, idx) => (
              <div key={idx} className="border border-[var(--hairline)] bg-[#e5ded0]/40 p-4 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase tracking-[0.1em] text-[#2c4a8f]">
                    Unit 0{idx + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeUnit(idx)}
                    className="text-[10px] uppercase text-[#767e8c] hover:text-[#141c2b] cursor-pointer"
                  >
                    Remove
                  </button>
                </div>
                <input
                  aria-label={`Unit ${idx + 1} title`}
                  value={u.title}
                  onChange={(e) => updateUnitTitle(idx, e.target.value)}
                  className="w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-1.5 text-xs font-bold"
                />
                <input
                  aria-label={`Unit ${idx + 1} topics`}
                  value={u.topics.join(", ")}
                  onChange={(e) => updateUnitTopics(idx, e.target.value)}
                  placeholder="Topic A, Topic B, Topic C"
                  className="w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-1.5 text-xs"
                />
              </div>
            ))}
          </div>
          <button type="button" onClick={addUnit} className="editorial-btn py-1.5 px-3 text-[11px]">
            + Add Unit
          </button>
        </div>
      ),
    },
    {
      id: "confirm",
      title: "Confirm & Save Chunks",
      subtitle: "Confirm your syllabus structure to index chunks in MySQL for TF-IDF retrieval.",
      content: (
        <div className="border border-[var(--hairline)] bg-[#e5ded0]/40 p-4 text-xs space-y-2">
          <p>
            <strong>Document:</strong> {activeDoc?.filename}
          </p>
          <p>
            <strong>Subject:</strong> {editableSubjectName}
          </p>
          <p>
            <strong>Units Configured:</strong> {editableUnits.length}
          </p>
          <p>
            <strong>Indexed Chunks Ready:</strong>{" "}
            {(activeDoc?.extracted_structure_json?.chunks || []).length}
          </p>
          <p className="text-[#4a5364]">
            Click "Confirm & Save Chunks" to persist this structure and switch to Practice Assessments.
          </p>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
            Syllabus Intelligence &amp; Assessment Lab
          </p>
          <h1 className="mt-2 font-editorial text-4xl font-normal text-[#141c2b]">
            Upload, Library &amp; Grounded Assessments
          </h1>
        </div>
        <div className="flex border border-[var(--hairline)] bg-[#e5ded0]">
          {(
            [
              ["upload", "01 Upload"],
              ["library", `02 Library (${docs.length})`],
              ["assessments", "03 Assessments"],
            ] as [LabTab, string][]
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => switchTab(id)}
              className={`px-4 py-2 text-[11px] uppercase tracking-[0.1em] cursor-pointer ${
                tab === id
                  ? "bg-[#efe9dd] font-bold text-[#2c4a8f] border-b-2 border-[#2c4a8f]"
                  : "text-[#4a5364] hover:text-[#141c2b]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {message && (
        <p className="border-l-2 border-[#2c4a8f] bg-[#e5ded0] p-3 text-xs">{message}</p>
      )}
      {error && (
        <p role="alert" className="border-l-2 border-[#141c2b] bg-[#e5ded0] p-3 text-xs">
          {error}
        </p>
      )}

      {/* TAB 1: UPLOAD */}
      {tab === "upload" && (
        <AnimatedStepper
          steps={stepperSteps}
          completeLabel="Confirm & Save Chunks"
          onComplete={confirmAndSaveChunks}
          submitting={saving}
        />
      )}

      {/* TAB 2: LIBRARY */}
      {tab === "library" && (
        <div className="border border-[var(--hairline)]">
          <div className="border-b border-[var(--hairline)] bg-[#e5ded0] px-4 py-3 text-[11px] uppercase tracking-[0.1em]">
            Uploaded Syllabus Library ({docs.length})
          </div>
          <div className="divide-y divide-[var(--hairline)]">
            {docs.length === 0 ? (
              <p className="p-6 text-xs text-[#767e8c]">
                No syllabus documents uploaded yet. Use the Upload tab to index a PDF or DOCX.
              </p>
            ) : (
              docs.map((d) => (
                <div key={d.id} className="flex flex-wrap items-center justify-between gap-4 p-4 text-xs bg-[#efe9dd]">
                  <div>
                    <p className="font-bold text-[#141c2b]">
                      {d.filename}{" "}
                      <span className="ml-2 text-[10px] uppercase text-[#2c4a8f]">
                        [{d.processing_status}]
                      </span>
                    </p>
                    <p className="mt-1 text-[11px] text-[#4a5364]">
                      {(d.extracted_structure_json?.units || []).length} units ·{" "}
                      {(d.extracted_structure_json?.chunks || []).length} TF-IDF chunks
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedDocId(d.id);
                      switchTab("assessments");
                    }}
                    className="editorial-btn py-1.5 px-3 text-[11px]"
                  >
                    Generate Assessment →
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 3: ASSESSMENTS */}
      {tab === "assessments" && (
        <div className="space-y-6">
          <div className="border border-[var(--hairline)] bg-[#e5ded0] p-5 space-y-4">
            <h2 className="font-editorial text-2xl text-[#141c2b]">
              TF-IDF + Gemini 2.5 Flash Practice Generator
            </h2>
            <p className="text-xs text-[#4a5364]">
              Retrieves top matching syllabus chunks via scikit-learn TfidfVectorizer and
              generates grounded MCQs (with automatic reviewed NIET bank fallback if Gemini is
              unavailable).
            </p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <label htmlFor="qz-subj" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Subject
                </label>
                <select
                  id="qz-subj"
                  value={selectedSubjectId}
                  onChange={(e) => {
                    setSelectedSubjectId(e.target.value);
                    setSelectedUnitId("");
                  }}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-2 text-xs"
                >
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.code} — {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="qz-unit" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Unit / Module
                </label>
                <select
                  id="qz-unit"
                  value={selectedUnitId}
                  onChange={(e) => setSelectedUnitId(e.target.value)}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-2 text-xs"
                >
                  <option value="">All Modules</option>
                  {(currentSubject?.units_topics || []).map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.order_index}. {u.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="qz-doc" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Uploaded Syllabus (Optional)
                </label>
                <select
                  id="qz-doc"
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="mt-1 w-full border border-[var(--hairline)] bg-[#efe9dd] px-3 py-2 text-xs"
                >
                  <option value="">Preloaded NIET Syllabus</option>
                  {docs.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.filename} ({d.processing_status})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="qz-count" className="block text-[10px] uppercase tracking-[0.1em] text-[#4a5364]">
                  Questions (5–10) &amp; Difficulty
                </label>
                <div className="mt-1 flex gap-2">
                  <input
                    id="qz-count"
                    type="number"
                    min={5}
                    max={10}
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(e.target.value)}
                    className="w-20 border border-[var(--hairline)] bg-[#efe9dd] px-2 py-2 text-xs"
                  />
                  <select
                    aria-label="Difficulty"
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="flex-1 border border-[var(--hairline)] bg-[#efe9dd] px-2 py-2 text-xs"
                  >
                    <option value="mixed">Mixed</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              type="button"
              disabled={saving}
              onClick={() => void generateAndStartQuiz()}
              className="editorial-btn editorial-btn-primary"
            >
              {saving ? "Retrieving Chunks & Generating..." : "Generate & Start Assessment"}
            </button>

            {genNotice && (
              <div className="border-l-2 border-[#2c4a8f] bg-[#efe9dd] px-4 py-2.5 text-xs text-[#141c2b]">
                <strong className="uppercase text-[#2c4a8f]">
                  [{genSource === "gemini_rag" ? "Gemini 2.5 Flash" : "Reviewed Bank Fallback"}]
                </strong>{" "}
                {genNotice}
              </div>
            )}
          </div>

          {quiz && quiz.status === "in_progress" && (
            <div className="border border-[var(--hairline)] bg-[#efe9dd] p-6 space-y-6">
              <div className="flex justify-between border-b border-[var(--hairline)] pb-3 text-xs">
                <span className="font-bold uppercase tracking-[0.1em]">Practice Assessment</span>
                <span>{quiz.questions.length} Questions</span>
              </div>
              {quiz.questions.map((q, idx) => (
                <div key={q.id} className="space-y-3 border-b border-[var(--hairline)] pb-5">
                  <p className="text-xs font-bold text-[#141c2b]">
                    {idx + 1}. {q.question_text}{" "}
                    <span className="ml-2 text-[10px] uppercase text-[#767e8c]">[{q.difficulty}]</span>
                  </p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {(q.options || []).map((opt) => (
                      <label
                        key={opt}
                        className={`flex items-center gap-2 border p-2.5 text-xs cursor-pointer ${
                          answers[q.id] === opt
                            ? "border-[#2c4a8f] bg-[#e5ded0] font-bold"
                            : "border-[var(--hairline)]"
                        }`}
                      >
                        <input
                          type="radio"
                          name={`q-${q.id}`}
                          checked={answers[q.id] === opt}
                          onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                        />
                        <span>{opt}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <button
                type="button"
                onClick={() => void submitQuiz()}
                className="editorial-btn editorial-btn-primary"
              >
                Submit Assessment
              </button>
            </div>
          )}

          {quiz && quiz.status === "submitted" && (
            <div className="border border-[var(--hairline)] bg-[#efe9dd] p-6 space-y-5">
              <h3 className="font-editorial text-3xl text-[#2c4a8f]">
                Score: {quiz.score} / {quiz.max_score}
              </h3>
              <div className="divide-y divide-[var(--hairline)] border-t border-[var(--hairline)]">
                {quiz.feedback.map((f, idx) => (
                  <div key={f.question_id} className="py-4 text-xs">
                    <p className="font-bold">
                      {idx + 1}. {f.question_text}
                    </p>
                    <p className="mt-1 text-[#4a5364]">
                      Your answer: <strong>{f.user_answer || "—"}</strong> · Correct:{" "}
                      <strong className="text-[#2c4a8f]">{f.correct_answer}</strong> (
                      {f.is_correct ? "Correct" : "Needs review"})
                    </p>
                    <p className="mt-1 text-[#767e8c]">{f.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
