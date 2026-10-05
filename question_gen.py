"""Skill-aware controlled question generation (v1).
No hallucination: curated bank + project templates. LLM hook optional later.
"""
import random

def skill_questions(skill: str):
    s = skill.title()
    return [
        (f"Explain the core concepts of {s} and where you have used it.", "conceptual"),
        (f"In {s}, describe a practical problem you solved. What approach and tools did you use?", "practical"),
        (f"Scenario: your {s} code fails in production. How do you debug and fix it?", "scenario"),
    ]

PROJECT_TEMPLATES = [
    "Explain your project: '{p}'. What was your role, tech stack, and biggest challenge?",
    "In project '{p}', what architecture/design decisions did you take and why?",
    "What would you improve in project '{p}' if you rebuilt it today (performance, scale, testing)?",
    "Deep-dive on '{p}': explain one hard bug or tradeoff and how you resolved it.",
]

HR_BANK = [
    "Tell me about yourself and walk me through your resume.",
    "Why should we hire you for this role? What are your key strengths?",
    "Describe a challenging team situation or conflict and how you handled it.",
    "Where do you see yourself in 2-3 years? How does this role fit?",
    "Tell me about a failure or mistake. What did you learn?",
    "How do you handle pressure or tight deadlines? Give an example.",
    "Do you have any questions for us about the team/role?",
]

def generate_technical(skills, projects, n=10):
    qs = []
    # 6 skill-based
    pool = []
    for s, _ in (skills or [("python", "skill")]):
        pool.extend([(q, s, d) for q, d in skill_questions(s)])
    random.seed(42)  # deterministic for college demo
    random.shuffle(pool)
    qs.extend(pool[:6])
    # 4 project-based
    projs = projects or ["your final year project"]
    short = []
    for p in projs:
        # shorten project ctx to a title-ish chunk
        title = p[:80].replace("\n", " ")
        short.append(title)
    pi = 0
    while len(qs) < n:
        t = PROJECT_TEMPLATES[(len(qs) - 6) % len(PROJECT_TEMPLATES)]
        p = short[pi % len(short)]
        qs.append((t.format(p=p), f"project:{p[:30]}", "project-deep"))
        pi += 1
    return [{"text": q, "skill_tag": tag, "difficulty": d} for q, tag, d in qs[:n]]

def generate_hr(n=6):
    return [{"text": q, "skill_tag": "hr", "difficulty": "behavioral"}
            for q in HR_BANK[:n]]
