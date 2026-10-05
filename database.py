"""SQLite storage for v1. Stores all previous interview questions + responses."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "interview.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT, email TEXT, resume_text TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS keywords (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id INTEGER, skill TEXT, source TEXT,
  FOREIGN KEY(candidate_id) REFERENCES candidates(id)
);
CREATE TABLE IF NOT EXISTS interviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id INTEGER, round TEXT, created_at TEXT,
  FOREIGN KEY(candidate_id) REFERENCES candidates(id)
);
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  interview_id INTEGER, text TEXT, skill_tag TEXT, difficulty TEXT,
  FOREIGN KEY(interview_id) REFERENCES interviews(id)
);
CREATE TABLE IF NOT EXISTS responses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER, transcript TEXT, score_json TEXT,
  FOREIGN KEY(question_id) REFERENCES questions(id)
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  interview_id INTEGER UNIQUE, overall REAL, summary TEXT, detail_json TEXT,
  FOREIGN KEY(interview_id) REFERENCES interviews(id)
);
"""

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript(SCHEMA)

def create_candidate(name, email, resume_text):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO candidates(name,email,resume_text,created_at) VALUES(?,?,?,?)",
            (name, email, resume_text, datetime.utcnow().isoformat()))
        return cur.lastrowid

def save_keywords(cid, items):
    with conn() as c:
        for skill, src in items:
            c.execute("INSERT INTO keywords(candidate_id,skill,source) VALUES(?,?,?)",
                      (cid, skill, src))

def create_interview(cid, rnd):
    with conn() as c:
        cur = c.execute("INSERT INTO interviews(candidate_id,round,created_at) VALUES(?,?,?)",
                        (cid, rnd, datetime.utcnow().isoformat()))
        return cur.lastrowid

def save_question(iid, text, tag, diff="medium"):
    with conn() as c:
        cur = c.execute("INSERT INTO questions(interview_id,text,skill_tag,difficulty) VALUES(?,?,?,?)",
                        (iid, text, tag, diff))
        return cur.lastrowid

def save_response(qid, transcript, score):
    with conn() as c:
        c.execute("INSERT INTO responses(question_id,transcript,score_json) VALUES(?,?,?)",
                  (qid, transcript, json.dumps(score)))

def save_feedback(iid, overall, summary, detail):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO feedback(interview_id,overall,summary,detail_json) VALUES(?,?,?,?)",
                  (iid, overall, summary, json.dumps(detail)))

def get_questions_by_interview(iid):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM questions WHERE interview_id=? ORDER BY id", (iid,))]

def get_history(cid):
    with conn() as c:
        rows = c.execute("""
          SELECT i.round, q.id qid, q.text qtext, q.skill_tag,
                 r.transcript, r.score_json, f.summary, f.overall
          FROM interviews i
          LEFT JOIN questions q ON q.interview_id=i.id
          LEFT JOIN responses r ON r.question_id=q.id
          LEFT JOIN feedback f ON f.interview_id=i.id
          WHERE i.candidate_id=? ORDER BY i.id, q.id
        """, (cid,)).fetchall()
        return [dict(r) for r in rows]

def get_feedback(iid):
    with conn() as c:
        r = c.execute("SELECT * FROM feedback WHERE interview_id=?", (iid,)).fetchone()
        return dict(r) if r else None
