# AI Interview v1

Resume -> keywords -> dynamic Qs (10 tech + 6 HR) -> text Q + voice answer -> eval -> DB + feedback.

## Run
```
pip install -r requirements.txt
uvicorn app:app --reload
```
Open http://127.0.0.1:8000

## Flow
1. Upload PDF/DOCX/TXT resume + name/email (`POST /api/upload`)
2. Technical round (10: 6 skill + 4 project) + HR round (6) - text display
3. Answer via mic (Web Speech API, Chrome best) or type
4. Submit (`POST /api/submit`) -> rubric scores + summary
5. History (`GET /api/history/{cid}`) - all previous Qs stored in sqlite `interview.db`

## Files
- `app.py` - FastAPI routes
- `resume_parser.py` - text extract + skills/projects
- `question_gen.py` - controlled bank (no hallucination)
- `evaluator.py` - heuristic rubric (swap with LLM later)
- `database.py` - sqlite schema
- `static/` - frontend

## v2 hook
Replace `static/app.js` mic (Web Speech) with Lychee-FD realtime session, keep `/api/*` unchanged.
