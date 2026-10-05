# AI Interview Response Evaluation System — v1 Detailed Docs

## 1. What this project does

Input resume (PDF/DOCX/TXT) → keyword extraction → dynamic questions
→ 2 interview rounds → voice answers → evaluation → DB + summarized feedback.

Spec coverage:

| Requirement | Implementation |
|---|---|
| Resume input, extract keywords | `resume_parser.py` — ~80-skill dictionary + project context lines |
| Dynamic questions from skills + projects | `question_gen.py` — 10 technical (6 skill + 4 project-deep) + 6 HR (spec allows 5–7) |
| Questions in text, answers voice-to-text | `static/index.html` + `static/app.js` — text display, Web Speech API (`en-IN`, interim preview), typing fallback |
| 2 rounds | Round 1 technical (10), Round 2 HR (6), switchable tabs |
| All previous questions in database | `database.py` + `interview.db` (SQLite) — candidates, keywords, interviews, questions, responses, feedback |
| Summarized feedback | `evaluator.py:summarize()` — overall /10, strengths, gaps, recommendation |

No API key needed. Everything runs locally on a student laptop.

## 2. Architecture

```
Browser (index.html/app.js)
  │ upload resume (multipart)      │ answers JSON
  ▼                                ▼
FastAPI (app.py)
  ├── resume_parser.extract_text + extract_keywords
  ├── question_gen.generate_technical / generate_hr
  ├── evaluator.evaluate_answer + summarize
  └── database (sqlite3, interview.db)
```

No separate ASR server in v1: speech-to-text happens in the browser
via Web Speech API. The backend only receives final transcripts.

## 3. Tech stack (and why)

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + Uvicorn | Simple REST, auto docs, multipart upload |
| Resume PDF | pypdf | Pure-python, no system deps |
| Resume DOCX | python-docx | Same reason |
| DB | SQLite (`sqlite3` stdlib) | Zero setup, file `interview.db`, all history queryable |
| STT | Web Speech API (browser) | Free, realtime interim results, no key/server |
| Q-gen | Curated bank + templates, `random.seed(42)` | Deterministic demo, no hallucination |
| Eval | Heuristic rubric | Deterministic, offline; `evaluate_answer()` is swappable with an LLM later |

Full pins: `requirements.txt` — fastapi 0.115.6, uvicorn 0.34.0,
python-multipart 0.0.20, pypdf 5.1.0, python-docx 1.1.2, httpx 0.28.1.

## 4. Project structure

```
Default Project/
├── app.py            # routes: /, /api/upload, /api/submit, /api/history/{cid}, /api/feedback/{iid}
├── resume_parser.py  # SKILLS list, extract_text(), extract_keywords() -> (skills[:12], projects[:3])
├── question_gen.py   # skill_questions(), PROJECT_TEMPLATES[4], HR_BANK[7], generate_technical(n=10), generate_hr(n=6)
├── evaluator.py      # evaluate_answer(), summarize()
├── database.py       # SCHEMA + helpers, DB_PATH=interview.db
├── static/
│   ├── index.html    # 3 cards: upload → interview → feedback
│   ├── app.js        # S-state, upload(), render(), toggleMic(), submitRound(), loadHistory()
│   └── style.css
├── requirements.txt
├── README.md         # short run guide
└── DOCS.md           # this file
```

## 5. Setup + all commands (Windows PowerShell)

```powershell
Set-Location -LiteralPath "C:\Users\Aditi\Documents\Default Project"
python --version
pip --version
pip install -r requirements.txt
uvicorn app:app --reload
# open http://127.0.0.1:8000
```

Variants:

```powershell
uvicorn app:app --reload --port 8001
uvicorn app:app --host 0.0.0.0 --port 8000   # test mic from phone on same WiFi
```

Stop server: `Ctrl + C`.

Reset demo data (deletes all history):

```powershell
Remove-Item -LiteralPath "interview.db" -Force
```

Inspect DB:

```powershell
python -c "import sqlite3; c=sqlite3.connect('interview.db'); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")])"
```

Health check (second terminal, server running):

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing | Select-Object StatusCode
```

Cleanup:

```powershell
Remove-Item -Recurse -Force "__pycache__" -ErrorAction SilentlyContinue
Get-ChildItem
```

## 6. API reference

### POST /api/upload (multipart/form-data)

Fields: `name` (text), `email` (text), `file` (PDF/DOCX/TXT).

Response:

```json
{
  "candidate_id": 1,
  "skills": ["python", "react", "sql"],
  "projects": ["Project: Chat app with React and FastAPI..."],
  "tech_interview_id": 1,
  "hr_interview_id": 2,
  "technical": [{"id": 1, "text": "...", "skill_tag": "python", "difficulty": "conceptual"}],
  "hr": [{"id": 11, "text": "...", "skill_tag": "hr", "difficulty": "behavioral"}]
}
```

Behavior: saves candidate (resume truncated to 8000 chars), keywords,
2 interviews, 16 questions. Technical falls back to `[("python","skill")]`
and project `"your final year project"` when resume has none.

### POST /api/submit (application/json)

```json
{"interview_id": 1, "answers": [{"question_id": 1, "transcript": "..."}]}
```

Behavior: unknown `question_id`s are skipped; each answer scored and saved;
per-interview feedback upserted (`INSERT OR REPLACE`). Returns the summary
object (see §8).

### GET /api/history/{candidate_id}

JOIN across interviews → questions → responses → feedback, ordered by
interview then question. Returns list of rows with
`round, qid, qtext, skill_tag, transcript, score_json, summary, overall`.
One candidate with both rounds submitted = 16 rows.

### GET /api/feedback/{interview_id}

Returns the `feedback` row or `{}` if the round was never submitted.

Interactive API docs (server running): http://127.0.0.1:8000/docs

## 7. Database schema

```sql
candidates(id, name, email, resume_text, created_at)
keywords(id, candidate_id → candidates, skill, source)
interviews(id, candidate_id → candidates, round, created_at)   -- round = 'technical' | 'hr'
questions(id, interview_id → interviews, text, skill_tag, difficulty)
responses(id, question_id → questions, transcript, score_json)
feedback(id, interview_id UNIQUE → interviews, overall, summary, detail_json)
```

## 8. Evaluation rubric (exact v1 logic)

Per answer (`evaluator.evaluate_answer`, all 0–10):

- **completeness** = `min(10, words/12)`, +1 if ≥3 sentences.
- **clarity** = 8 if avg sentence length 6–30 words else 6; 4 if <10 words total.
- **relevance** = `min(10, 2 + overlap*12)` where overlap = question keywords (≥4 chars) ∩ answer words.
- **accuracy/coverage proxy** = `min(10, 3 + tech_hits*1.2 + min(2, words/60))`,
  tech_hits counts api|database|model|function|class|test|deploy|server|client|algorithm|design|error|debug|performance|scale|project|team|learn.
- **overall** = mean of the four, rounded to 1 decimal. Empty answer = all zeros.

Summary (`evaluator.summarize`):

- overall = mean of per-question overall.
- strengths = questions scoring ≥7 (kept 5 max); gaps = scoring <5 (kept 5 max).
- recommendation: ≥7.5 Strong Hire · ≥6 Hire · ≥4.5 Borderline · else No Hire.
- summary string includes overall, technical/HR split avgs when both present, verdict, counts.

To plug in an LLM later, replace only `evaluate_answer()` — keep its
return keys (`accuracy, completeness, clarity, relevance, overall, explanation`).

## 9. Frontend + voice flow

1. Card 1: enter name/email, choose file, **Parse + Generate** → `upload()`
   shows `Skills: ...`, loads technical round.
2. Card 2: tabs Technical (10) / HR (6) / History. `qbox` shows
   `Q{i}/{n}: text`. `Save & Next` stores the textarea into `S.answers[qid]`
   (switching tabs resets index to 0 but keeps saved answers).
3. Mic: `toggleMic()` uses `SpeechRecognition || webkitSpeechRecognition`,
   `lang='en-IN'`, `interimResults=true`, `continuous=true`; live preview
   goes into the textarea; **Stop** ends it. Not supported (e.g. Firefox) →
   alert, type instead. Chrome/Edge recommended; mic needs localhost or HTTPS.
4. **Submit round** saves the current textarea, POSTs only answers belonging
   to the visible round, renders `overall/summary/recommendation/strengths/gaps`.
5. **History** dumps first 30 history rows as JSON into `<pre>`.

## 10. Demo script (2 minutes)

1. `uvicorn app:app --reload`, open http://127.0.0.1:8000.
2. Upload a TXT resume containing e.g.
   `Python, React, SQL developer. Project: Chat app with React and FastAPI.`
3. Confirm skills appear; step through 10 technical Qs speaking 2–3 sentences
   each (mention tech words: api, test, deploy, performance), Save & Next.
4. Submit → expect ~6/10 Hire on substantive answers.
5. Switch to HR tab, answer 6, submit.
6. History → 16 rows. Show `interview.db` tables for the DB requirement.

## 11. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Mic does nothing / alert | Browser lacks SpeechRecognition → use Chrome/Edge; serve via localhost/HTTPS and allow mic permission |
| `WinError 32 ... interview.db` on delete | Server still running → `Ctrl+C` the uvicorn terminal first, then delete |
| PDF gives no skills | Scanned-image PDF has no text layer → use DOCX/TXT or OCR the PDF first |
| Questions feel repetitive | Deterministic `seed(42)` bank — by design for demo; extend `SKILLS`/`HR_BANK` or add LLM paraphrase |
| Port busy | `uvicorn app:app --reload --port 8001` |
| `__pycache__` noise | `Remove-Item -Recurse -Force __pycache__` |

## 12. Limits + v2 path

v1 limits: dictionary skills (no SBERT/NER), template questions (no LLM
generation), heuristic scores (no semantic judge), browser STT only
(accent/noise sensitive, Chrome-centric), SQLite single-file.

v2 (Lychee-FD full-duplex voice) keeps this backend intact: replace only
`static/app.js` mic/post logic with a Lychee realtime session; keep
`/api/upload`, `/api/submit`, `/api/history` unchanged so resume → questions
→ DB → feedback logic is reused.
