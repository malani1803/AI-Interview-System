# AI Interview System (v1)

An AI-based interview response evaluation system: upload a resume,
get dynamic technical + HR questions, answer by voice, get scored
feedback — with every question stored in a database.

```
Resume (PDF/DOCX/TXT) → keywords → 10 tech + 6 HR questions
→ text Q + voice answer → rubric eval → SQLite + summarized feedback
```

No API key needed. Runs fully offline on a laptop
(except the browser's built-in speech recognition).

## Features

- **Resume parsing** — extracts text from PDF (`pypdf`), DOCX (`python-docx`),
  or TXT; matches ~80 skills (Python, React, SQL, Docker, AWS, ML, …)
  plus project/internship context lines.
- **Dynamic questions, no hallucination** — curated skill bank
  (conceptual / practical / scenario per skill) + 4 project deep-dive
  templates + 7-question HR bank. Deterministic (`seed 42`) so demos
  are reproducible.
- **Two rounds** — Technical (10: 6 skill + 4 project) and HR (6, spec allows 5–7),
  switchable tabs in one page.
- **Text questions, voice answers** — questions render as text; answers are
  captured with the browser Web Speech API (`en-IN`, live interim preview)
  with a typing fallback (Chrome/Edge recommended).
- **Evaluation + feedback** — per-answer scores on accuracy, completeness,
  clarity, relevance (0–10) plus overall average, strengths (≥7),
  gaps (<5), and a verdict: Strong Hire / Hire / Borderline / No Hire.
- **Database history** — SQLite (`interview.db`): candidates, keywords,
  interviews, questions, responses, feedback. `GET /api/history/{id}`
  returns all previous questions for a candidate.

## Quickstart (Windows PowerShell)

```powershell
Set-Location -LiteralPath "C:\Users\Aditi\Documents\Default Project"
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 (allow mic access when asked).
Stop the server with `Ctrl + C`.

| Variant | Command |
|---|---|
| Different port | `uvicorn app:app --reload --port 8001` |
| Test mic from phone (same WiFi) | `uvicorn app:app --host 0.0.0.0 --port 8000` |
| Fresh demo (wipe history) | `Remove-Item -LiteralPath "interview.db" -Force` (server stopped first) |

Requirements: Python 3.10+ (tested 3.13), mic + Chrome/Edge for voice.

## Usage walkthrough

1. **Upload** — enter name/email, choose resume file,
   click **Parse + Generate Questions**. Skills appear (e.g. `python, react, sql`).
2. **Technical round** — Q1/10 … Q10/10 shown as text. Click **🎤 Start voice**,
   speak 2–3 sentences per answer (mention concrete tech words like api, test,
   deploy, performance), **⏹ Stop**, **Save & Next**. Or just type.
3. **Submit round** — **Submit round for evaluation** scores it and shows
   `overall/10 + summary + recommendation + strengths + gaps`.
4. **HR round** — switch tab, answer 6 behavioral questions, submit.
5. **History** — **History (DB)** dumps stored questions/transcripts/scores.

Tip for good scores: 30+ words, 3+ sentences, overlap with the question's
keywords, concrete details (tools, numbers, tradeoffs).

## API reference

Interactive docs while running: http://127.0.0.1:8000/docs

**`POST /api/upload`** (multipart: `name`, `email`, `file`)
→ `{candidate_id, skills[], projects[], tech_interview_id, hr_interview_id,
technical[10 × {id, text, skill_tag, difficulty}], hr[6 × …]}`.
Empty resumes fall back to Python + "final year project" so the flow never breaks.

**`POST /api/submit`** (JSON: `{interview_id, answers: [{question_id, transcript}]}`)
→ `{overall, summary, strengths[], gaps[], recommendation, per_question[]}`.
Unknown question IDs are skipped; feedback is upserted per interview.

**`GET /api/history/{candidate_id}`** → all rows (interviews ⨝ questions ⨝
responses ⨝ feedback), 16 rows after both rounds.

**`GET /api/feedback/{interview_id}`** → saved feedback row or `{}`.

## Scoring rubric

Per answer (0–10 each, mean = overall):
- **completeness** — `words/12` capped at 10, +1 for ≥3 sentences
- **clarity** — 8 for 6–30 words/sentence, else 6 (4 if <10 words total)
- **relevance** — keyword overlap with the question
- **accuracy/coverage** — technical-term hits + length

Verdicts: ≥7.5 Strong Hire · ≥6 Hire · ≥4.5 Borderline · else No Hire.
To upgrade to LLM judging later, replace only `evaluate_answer()` in
`evaluator.py` — its return keys stay the same.

## Project structure

```
app.py            # FastAPI routes
resume_parser.py  # extract_text(), extract_keywords() → skills[:12], projects[:3]
question_gen.py   # skill bank, project templates, HR bank
evaluator.py      # evaluate_answer(), summarize()
database.py       # SQLite schema + helpers (interview.db)
static/           # index.html, app.js (state + mic), style.css
requirements.txt  # pinned deps
DOCS.md           # deep-dive documentation
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Mic does nothing | Use Chrome/Edge on localhost/HTTPS, allow mic permission; otherwise type |
| `WinError 32 … interview.db` | Stop the server (`Ctrl+C`) before deleting the DB |
| PDF yields no skills | Scanned-image PDFs have no text — use DOCX/TXT |
| Port busy | `--port 8001` |
| Same questions every time | By design (`seed 42`); extend `SKILLS`/`HR_BANK` or add LLM paraphrase |

## Roadmap (v2)

Swap the browser mic layer (`static/app.js`) for a Lychee-FD full-duplex
voice session (barge-in, natural turn-taking, self-hosted) while keeping
`/api/*`, the DB, and the evaluator unchanged. See `DOCS.md` §12.
