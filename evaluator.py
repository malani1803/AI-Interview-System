"""Heuristic rubric evaluator (v1). Deterministic, no API key needed.
Dimensions 0-10: accuracy/coverage, completeness, clarity, relevance.
LLM-eval can replace evaluate_answer() later without changing API.
"""
import re

def evaluate_answer(question: str, answer: str, skill_tag: str = ""):
    a = (answer or "").strip()
    words = re.findall(r"\w+", a.lower())
    n = len(words)
    sentences = [s for s in re.split(r"[.!?]+", a) if s.strip()]

    if n == 0:
        return {"accuracy": 0, "completeness": 0, "clarity": 0, "relevance": 0,
                "overall": 0, "explanation": "No answer provided."}

    # completeness: length + sentences (cap at ~120 words ideal)
    completeness = min(10, round(n / 12, 1))
    if len(sentences) >= 3:
        completeness = min(10, completeness + 1)

    # clarity: avg sentence length sane + punctuation
    avg_len = n / max(1, len(sentences))
    clarity = 8 if 6 <= avg_len <= 30 else 6
    if n < 10:
        clarity = 4

    # relevance: overlap with question keywords
    qkeys = set(re.findall(r"\w{4,}", question.lower()))
    akeys = set(words)
    overlap = len(qkeys & akeys) / max(1, len(qkeys))
    relevance = round(min(10, 2 + overlap * 12), 1)

    # accuracy/coverage proxy: technical terms + specificity (numbers, tech words)
    tech_hits = len(re.findall(
        r"api|database|model|function|class|test|deploy|server|client|algorithm|design|error|debug|performance|scale|project|team|learn", a.lower()))
    accuracy = round(min(10, 3 + tech_hits * 1.2 + min(2, n / 60)), 1)

    overall = round((accuracy + completeness + clarity + relevance) / 4, 1)
    expl = (f"{n} words, {len(sentences)} sentences. "
            f"Coverage {accuracy}/10, completeness {completeness}/10, "
            f"clarity {clarity}/10, relevance {relevance}/10.")
    return {"accuracy": accuracy, "completeness": completeness, "clarity": clarity,
            "relevance": relevance, "overall": overall, "explanation": expl}

def summarize(responses):
    """responses: list of {question, skill_tag, transcript, score}"""
    if not responses:
        return {"overall": 0, "summary": "No responses.", "strengths": [], "gaps": [],
                "recommendation": "No Hire", "per_question": []}
    avg = round(sum(r["score"]["overall"] for r in responses) / len(responses), 1)
    tech = [r for r in responses if r.get("skill_tag") != "hr"]
    hr = [r for r in responses if r.get("skill_tag") == "hr"]
    strengths, gaps = [], []
    for r in responses:
        if r["score"]["overall"] >= 7:
            strengths.append(f"{r['skill_tag']}: {r['question'][:60]}...")
        elif r["score"]["overall"] < 5:
            gaps.append(f"{r['skill_tag']}: {r['question'][:60]}...")
    if avg >= 7.5:
        rec = "Strong Hire"
    elif avg >= 6:
        rec = "Hire"
    elif avg >= 4.5:
        rec = "Borderline - second opinion needed"
    else:
        rec = "No Hire"
    t_avg = round(sum(r["score"]["overall"] for r in tech) / max(1, len(tech)), 1) if tech else None
    h_avg = round(sum(r["score"]["overall"] for r in hr) / max(1, len(hr)), 1) if hr else None
    summary = (f"Candidate scored {avg}/10 overall"
               + (f" (Technical {t_avg}, HR {h_avg})" if t_avg is not None and h_avg is not None else "")
               + f". {rec}. "
               + (f"Strong in {len(strengths)} areas. " if strengths else "")
               + (f"Needs work in {len(gaps)} areas." if gaps else "Consistent performance."))
    return {"overall": avg, "summary": summary, "strengths": strengths[:5],
            "gaps": gaps[:5], "recommendation": rec,
            "per_question": [{"q": r["question"], "score": r["score"]["overall"],
                              "explain": r["score"]["explanation"]} for r in responses]}
