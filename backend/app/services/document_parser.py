"""Syllabus text extraction, validation, chunking, and TF-IDF chunk retrieval."""

from __future__ import annotations

from pathlib import Path
import re
import zipfile


def validate_uploaded_file(raw: bytes, ext: str, max_mb: int = 5) -> None:
    """Validate file size, non-empty content, and container magic bytes."""
    if not raw:
        raise ValueError("Uploaded file is empty.")
    max_bytes = max_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise ValueError(f"File exceeds the {max_mb} MB upload limit.")

    clean_ext = ext.lower().lstrip(".")
    if clean_ext == "pdf":
        if not raw.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file: missing %PDF- header signature.")
    elif clean_ext == "docx":
        if not raw.startswith(b"PK\x03\x04"):
            raise ValueError("Invalid DOCX file: expected ZIP archive signature.")
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise ValueError("Invalid DOCX archive: missing word/document.xml.")
        except zipfile.BadZipFile as exc:
            raise ValueError("Corrupted DOCX archive.") from exc
    elif clean_ext in {"txt", "md"}:
        pass
    else:
        raise ValueError("Unsupported file format. Upload a PDF or DOCX (or TXT/MD) syllabus.")


def clean_extracted_text(text: str) -> str:
    """Normalize line endings and collapse excessive blank lines/whitespace."""
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.replace("\r\n", "\n").splitlines()]
    cleaned_lines = [ln for ln in lines if ln]
    return "\n".join(cleaned_lines)


def extract_text_from_file(file_path: Path, file_type: str) -> str:
    """Extract clean readable text from PDF (PyMuPDF), DOCX (python-docx), or TXT/MD."""
    ext = file_type.lower().lstrip(".")
    if ext in {"txt", "md"}:
        return clean_extracted_text(file_path.read_text(encoding="utf-8", errors="ignore"))

    if ext == "pdf":
        import fitz  # PyMuPDF

        chunks: list[str] = []
        with fitz.open(str(file_path)) as doc:
            for page in doc:
                chunks.append(page.get_text("text"))
        return clean_extracted_text("\n".join(chunks))

    if ext == "docx":
        import docx

        document = docx.Document(str(file_path))
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        return clean_extracted_text("\n".join(paragraphs))

    raise ValueError(f"Unsupported syllabus file type: {file_type}")


def chunk_syllabus_text(text: str, chunk_size: int = 550, overlap: int = 80) -> list[str]:
    """Split clean syllabus text into overlapping chunks for TF-IDF retrieval."""
    if not text.strip():
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    chunks: list[str] = []
    buffer = ""

    for line in lines:
        candidate = f"{buffer}\n{line}".strip() if buffer else line
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
                tail = buffer[-overlap:] if len(buffer) > overlap else buffer
                buffer = f"{tail}\n{line}".strip()
            else:
                # Single very long line: slice cleanly
                for i in range(0, len(line), max(1, chunk_size - overlap)):
                    chunks.append(line[i : i + chunk_size])
                buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks


def retrieve_relevant_chunks(chunks: list[str], query: str, top_k: int = 5) -> list[str]:
    """Rank syllabus chunks against the selected unit/query using scikit-learn TfidfVectorizer."""
    if not chunks:
        return []
    if len(chunks) <= top_k or not query.strip():
        return chunks[:top_k]

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        corpus = chunks + [query]
        tfidf_matrix = vectorizer.fit_transform(corpus)
        sims = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
        ranked_indices = sims.argsort()[::-1][:top_k]
        return [chunks[int(i)] for i in ranked_indices]
    except ValueError:
        return chunks[:top_k]


def fallback_extract_structure(text: str, subject_name: str = "Uploaded Syllabus") -> dict:
    """Deterministic unit/topic parser used when Gemini is unavailable."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    units: list[dict] = []
    current_unit: dict | None = None

    unit_pattern = re.compile(
        r"^(unit|module|chapter)\s*[-:]?\s*(\d+|[ivx]+)?\s*[:.-]?\s*(.+)$", re.I
    )

    for line in lines:
        match = unit_pattern.match(line)
        if match:
            title = match.group(3).strip() or line
            current_unit = {"title": title[:200], "topics": []}
            units.append(current_unit)
        elif current_unit is not None and len(line) < 180:
            cleaned = line.lstrip("-*•0123456789. ")
            if cleaned:
                current_unit["topics"].append(cleaned)

    if not units:
        sample_topics = [ln.lstrip("-*• ")[:140] for ln in lines[:8] if len(ln) > 3]
        units = [
            {
                "title": f"{subject_name} — Core Module",
                "topics": sample_topics or ["Foundational Concepts", "Core Applications"],
            }
        ]

    return {"subject_name": subject_name, "units": units}
