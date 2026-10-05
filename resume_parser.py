"""Resume text extraction + skill/project keyword extraction (v1, no heavy ML)."""
import re
from io import BytesIO

SKILLS = [
    "python","java","c++","c","javascript","typescript","react","angular","vue",
    "node.js","nodejs","express","django","flask","fastapi","spring","spring boot",
    "sql","mysql","postgresql","mongodb","sqlite","redis",
    "html","css","tailwind","bootstrap",
    "machine learning","deep learning","nlp","computer vision","tensorflow","pytorch",
    "scikit-learn","pandas","numpy","data analysis","power bi","tableau","excel",
    "aws","azure","gcp","docker","kubernetes","jenkins","git","github","linux",
    "rest api","graphql","microservices","kafka","rabbitmq",
    "oops","dsa","data structures","algorithms","dbms","os","operating systems",
    "computer networks","cn","selenium","testing","jest","pytest",
    "figma","ui/ux","agile","scrum","jira",
    "c#",".net","php","laravel","ruby","rails","go","golang","rust","kotlin","swift","flutter",
]

def extract_text(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        r = PdfReader(BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in r.pages)
    if name.endswith(".docx"):
        from docx import Document
        d = Document(BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    # fallback: try utf-8
    return data.decode("utf-8", errors="ignore")

def extract_keywords(text: str):
    low = text.lower()
    found = []
    for s in SKILLS:
        # word-boundary-ish match
        if re.search(r"(?<![a-z0-9+#.])" + re.escape(s) + r"(?![a-z0-9+#.])", low):
            found.append((s, "skill"))
    # projects: lines mentioning project/internship + next line as context
    projects = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, l in enumerate(lines):
        if re.search(r"project|internship|capstone|major project|minor project", l, re.I):
            ctx = " ".join(lines[i:i+3])[:300]
            if len(ctx) > 20:
                projects.append(ctx)
    # dedupe, cap
    seen, uniq = set(), []
    for s, src in found:
        if s not in seen:
            seen.add(s); uniq.append((s, src))
    return uniq[:12], projects[:3]
