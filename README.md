# Scholia — AI-Based Academic Performance Predictor & Academic Intelligence Platform

Full-stack monorepo built for **PBL — Innovation and Entrepreneurship (NIET B.Tech CSE Data Science, Team A11)**.

## Stack

- **Frontend (`/frontend`):** React, Vite, TypeScript, Tailwind CSS v4, React Router, Recharts, GSAP + ScrollTrigger, Framer Motion, Lucide React, `qrcode.react`
- **Backend (`/backend`):** FastAPI, SQLAlchemy 2.0, PyMySQL, Alembic, Pydantic v2, bcrypt, python-jose, Scikit-learn, PyMuPDF (`fitz`), `python-docx`, Google Gemini API (`google-genai`, `gemini-2.5-flash`)
- **Database:** MySQL 8+ (11 normalized tables: `users`, `student_profiles`, `subjects`, `units_topics`, `assessments`, `assessment_results`, `attendance_records`, `predictions`, `syllabus_documents`, `questions`, `quiz_attempts`)

---

## Local Development Setup

### 1. Environment Variables
Copy `.env.example` to `.env` in the repository root and set your credentials:

```bash
cp .env.example .env
```

Required keys:
- `DATABASE_URL` — e.g. `mysql+pymysql://root:password@localhost:3306/academic_intelligence`
- `JWT_SECRET` — random secret key (32+ chars)
- `GEMINI_API_KEY` — Google Gemini API key (optional; reviewed NIET question-bank fallback runs automatically when unset or rate-limited)
- `FRONTEND_URL` — e.g. `http://localhost:5173`
- `VITE_API_URL` — e.g. `http://localhost:8000/api/v1`

### 2. Database & Backend (`/backend`)

Create the MySQL database (`CREATE DATABASE academic_intelligence CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`), then run:

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python ml/train_model.py
python seed_niet_sem1.py
python seed_classroom_questions.py
uvicorn app.main:app --reload --port 8000
```

Run backend tests:

```bash
cd backend
pytest -v
```

### 3. Frontend (`/frontend`)

```bash
cd frontend
npm install
npm run dev
```

Verify production build:

```bash
cd frontend
npm run build
```

---

## Production Deployment

### Backend on Render (using `render.yaml` / `backend/Procfile`)
1. Provision a managed MySQL 8+ instance (e.g., Aiven, PlanetScale/MySQL, AWS RDS, or Railway MySQL).
2. Create a Render Web Service from this repository (Render automatically detects `render.yaml`, or set **Root Directory** to `backend`, **Build Command** to `pip install -r requirements.txt && python ml/train_model.py`, and **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
3. Set environment variables on Render: `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`, and `FRONTEND_URL` (your deployed Vercel URL).
4. Run one-time migration & seed against the production database:
   ```bash
   alembic upgrade head
   python seed_niet_sem1.py
   python seed_classroom_questions.py
   ```

### Frontend on Vercel (using `frontend/vercel.json`)
1. Import the repository into Vercel and set **Root Directory** to `frontend`.
2. Add environment variable `VITE_API_URL` pointing to your Render backend URL (e.g. `https://academic-intelligence-api.onrender.com/api/v1`).
3. Deploy — `frontend/vercel.json` handles SPA rewrites so direct links and refreshes on `/classroom-challenge` and `/classroom-challenge/projector` never return 404.
