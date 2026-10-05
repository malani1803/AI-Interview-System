"""v1 FastAPI backend: resume upload -> Q-gen -> voice answers -> eval -> feedback."""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

import database as db
import resume_parser as rp
import question_gen as qg
import evaluator as ev

app = FastAPI(title="AI Interview v1")
db.init_db()
BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

class SubmitItem(BaseModel):
    question_id: int
    transcript: str

class SubmitReq(BaseModel):
    interview_id: int
    answers: list[SubmitItem]

@app.post("/api/upload")
async def upload(name: str = Form(""), email: str = Form(""),
                 file: UploadFile = File(...)):
    data = await file.read()
    text = rp.extract_text(data, file.filename or "resume.pdf")
    skills, projects = rp.extract_keywords(text)
    cid = db.create_candidate(name, email, text[:8000])
    db.save_keywords(cid, skills)

    tech_qs = qg.generate_technical(skills, projects, 10)
    hr_qs = qg.generate_hr(6)

    tech_id = db.create_interview(cid, "technical")
    hr_id = db.create_interview(cid, "hr")
    tq = [{"id": db.save_question(tech_id, q["text"], q["skill_tag"], q["difficulty"]), **q}
          for q in tech_qs]
    hq = [{"id": db.save_question(hr_id, q["text"], q["skill_tag"], q["difficulty"]), **q}
          for q in hr_qs]
    return {"candidate_id": cid,
            "skills": [s for s, _ in skills], "projects": projects,
            "tech_interview_id": tech_id, "hr_interview_id": hr_id,
            "technical": tq, "hr": hq}

@app.get("/api/default-questions")
def defaults():
    """Hardcoded sets shown before any upload (no DB writes)."""
    return {"technical": qg.get_default_technical(), "hr": qg.generate_hr(6)}

@app.post("/api/submit")
def submit(req: SubmitReq):
    qs = {q["id"]: q for q in db.get_questions_by_interview(req.interview_id)}
    results = []
    for a in req.answers:
        q = qs.get(a.question_id)
        if not q:
            continue
        score = ev.evaluate_answer(q["text"], a.transcript, q["skill_tag"])
        db.save_response(a.question_id, a.transcript, score)
        results.append({"question": q["text"], "skill_tag": q["skill_tag"],
                        "transcript": a.transcript, "score": score})
    summary = ev.summarize(results)
    db.save_feedback(req.interview_id, summary["overall"], summary["summary"], summary)
    return summary

@app.get("/api/history/{cid}")
def history(cid: int):
    return db.get_history(cid)

@app.get("/api/feedback/{iid}")
def feedback(iid: int):
    return db.get_feedback(iid) or {}
