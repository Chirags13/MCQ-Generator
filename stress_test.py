import sys
import os
import json
import re
from datetime import datetime

# Ensure project path (adjust if your project is in a different folder)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import the pipeline run_system function
try:
    from orchestrator.orchestrator import run_system
except Exception as e:
    print("ERROR importing run_system from orchestrator:", e)
    print("Make sure to run this script from the project root where orchestrator package is available.")
    raise

# Path to the uploaded file mentioned in the chat (developer instruction)
# We'll expose this as a local file URL inside the stress test report so judges/you can reference it.
UPLOADED_FILE_URL = "file:///mnt/data/8de4e9b0-74c7-4f32-b7ab-b4ddb8ce0b2f.png"

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
RESULT_FILE = os.path.join(OUTPUT_DIR, "stress_test_results.json")

# Curated topics to test various failure modes
TEST_TOPICS = [
    # Hallucination-prone / fictional
    "Zygoraxian fusion reactor operation principles",
    "Describe Nikola Tesla's secret communication with aliens",
    "Biology and life-cycle of dragons",
    # Ambiguous / disambiguation issues
    "Apple",
    "Java",
    # Numeric / arithmetic reasoning
    "Calculate speed if a car travels 150 km in 2 hours",
    "What is 17 * 42 + 11?",
    "Ohm's Law: V=12, R=3, find current",
    # Story-based reasoning
    "John gave his book to Mary, Mary gave it to Sarah. Who has the book?",
    "Tom is older than Sam, Sam is older than Lily. Who is the oldest?",
    # Contradictory / controversial
    "Is Pluto a planet?",
    "Who invented calculus? Newton or Leibniz?",
    # Long-context / heavy content
    "Provide a detailed chronology of World War II and produce 3 MCQs",
    # Real-world factual check
    "Photosynthesis",
    # Edge cases / special characters
    "Jungkook's impact on K-pop ❤️",
    # Mixed numeric + reasoning
    "A train leaves station A at 7 PM traveling at 60 km/h and reaches station B 210 km away. When does it arrive?",
    # Repetition to test non-determinism
    "Photosynthesis",
    "Photosynthesis",
    "Photosynthesis",
]

# Heuristic detectors
def detect_hallucination_text(text):
    if not text:
        return True
    low = text.lower()
    hallmarks = [
        "no reliable", "no evidence", "cannot be verified", "fictional", "imaginary",
        "there is no information", "unknown", "not found", "made up", "invented",
    ]
    for h in hallmarks:
        if h in low:
            return True
    # check for unusual tokens
    weird_tokens = re.findall(r"[A-Z][a-z]{5,}", text)
    if len(weird_tokens) >= 2:
        for w in weird_tokens:
            if w.lower() not in ["photosynthesis", "world", "war", "oxygen", "carbon", "photosynthetic"]:
                return True
    return False

def extract_numbers(s):
    return list(map(float, re.findall(r"(-?\\d+\\.?\\d*)", s)))

def numeric_consistency_check(question, solution_text):
    q = question.lower()
    m = re.search(r"(\\d+\\.?\\d*)\\s*(?:km|kilometers)\\s*(?:in|over)\\s*(\\d+\\.?\\d*)\\s*hours?", q)
    if m:
        dist = float(m.group(1))
        time_h = float(m.group(2))
        expected_speed = dist / time_h if time_h != 0 else None
        nums = extract_numbers(solution_text)
        if expected_speed is None:
            return False, "time zero"
        for n in nums:
            if abs(n - expected_speed) < 0.01 * max(1, expected_speed):
                return True, "speed match"
        return False, f"expected {expected_speed}, solver_numbers={nums}"

    m2 = re.search(r"what is\\s*([0-9\\.\\s\\+\\-\\*\\/\\(\\)]+)\\?", q)
    if m2:
        expr = m2.group(1)
        try:
            if re.match(r"^[0-9\\.\\s\\+\\-\\*\\/\\(\\)]+$", expr):
                expected = eval(expr)
                nums = extract_numbers(solution_text)
                for n in nums:
                    if abs(n - expected) < 0.01 * max(1, abs(expected)):
                        return True, "arithmetic match"
                return False, f"expected {expected}, solver_numbers={nums}"
        except Exception as e:
            return False, f"eval error {e}"

    m3 = re.search(r"v\\s*=\\s*(\\d+\\.?\\d*)\\D+r\\s*=\\s*(\\d+\\.?\\d*)", q)
    if m3:
        v = float(m3.group(1)); r=float(m3.group(2))
        expected = v / r if r != 0 else None
        nums = extract_numbers(solution_text)
        for n in nums:
            if expected is not None and abs(n - expected) < 0.01 * max(1, expected):
                return True, "ohm match"
        return False, f"expected {expected}, solver_numbers={nums}"

    m4 = re.search(r"(\\d+\\.?\\d*)\\s*km away.*?at\\s*(\\d+\\.?\\d*)\\s*km\\/h", q)
    if m4:
        dist=float(m4.group(1)); speed=float(m4.group(2))
        expected_time_hours = dist / speed if speed != 0 else None
        nums = extract_numbers(solution_text)
        if expected_time_hours is None:
            return False, "speed zero"
        for n in nums:
            if abs(n - expected_time_hours) < 0.5:
                return True, "arrival time numeric match"
        return False, f"expected_hours~{expected_time_hours}, solver_numbers={nums}"

    return None, "no numeric pattern"

def detect_disagreement(mcq, solution):
    try:
        gen_ans = str(mcq.get("answer", "")).strip()
        sol_ans = str(solution.get("chosen_answer", "")).strip()
        if gen_ans and sol_ans and gen_ans.lower() != sol_ans.lower():
            return True
        return False
    except Exception:
        return True

def detect_story_contradiction(question, explanation):
    q=qclean = str(question).lower()
    expl = str(explanation).lower() if explanation else ""
    if "who has the book" in q:
        if "sarah" in expl or "mary" in expl or "john" in expl:
            return False
        return True
    if "who is the oldest" in q:
        if "tom" in expl or "lily" in expl or "sam" in expl:
            return False
        return True
    if any(w in expl for w in ["contradict", "but then", "however", "inconsistent"]):
        return True
    return False

def simple_hallucination_checker(mcq, research_notes, solution, validation):
    reasons = []
    if detect_hallucination_text(research_notes):
        reasons.append("hallucination_in_research")
    if not isinstance(mcq, dict):
        reasons.append("mcq_not_dict")
    else:
        if "question" not in mcq or "options" not in mcq or "answer" not in mcq:
            reasons.append("mcq_schema_missing")
    if isinstance(validation, dict) and validation.get("valid") is False:
        reasons.append("validator_rejected")
    return reasons

results = []
summary = {"total": len(TEST_TOPICS), "pass": 0, "fail": 0, "details": []}

for idx, topic in enumerate(TEST_TOPICS, start=1):
    print(f"---\\nRUN {idx}/{len(TEST_TOPICS)}: {topic}\\n---")
    start = datetime.utcnow().isoformat() + "Z"
    try:
        out = run_system(topic)
    except Exception as e:
        out = {"error": f"exception during pipeline: {e}"}
    end = datetime.utcnow().isoformat() + "Z"

    entry = {
        "topic": topic,
        "start": start,
        "end": end,
        "result": out,
        "checks": [],
        "status": "unknown"
    }

    if "error" in out:
        entry["checks"].append({"type": "pipeline_error", "detail": out["error"]})
        entry["status"] = "fail"
        results.append(entry)
        summary["fail"] += 1
        continue

    research = out.get("research_notes", "") or ""
    mcqs = out.get("mcqs", [])
    sols = out.get("solutions", [])
    vals = out.get("validations", [])

    hallu_reasons = simple_hallucination_checker(mcqs[0] if mcqs else None, research, sols[0] if sols else None, vals[0] if vals else None)
    if hallu_reasons:
        entry["checks"].append({"type": "hallucination_checks", "detail": hallu_reasons})

    all_ok = True
    for i, mcq in enumerate(mcqs):
        sol = sols[i] if i < len(sols) else {}
        val = vals[i] if i < len(vals) else {}

        qtext = mcq.get("question", "") if isinstance(mcq, dict) else str(mcq)
        sol_text = json.dumps(sol) if isinstance(sol, dict) else str(sol)
        val_text = json.dumps(val) if isinstance(val, dict) else str(val)

        if not isinstance(mcq, dict):
            entry["checks"].append({"mcq_index": i, "type": "schema", "detail": "mcq not dict"})
            all_ok = False
            continue

        if "question" not in mcq or "options" not in mcq or "answer" not in mcq:
            entry["checks"].append({"mcq_index": i, "type": "schema", "detail": "missing fields"})
            all_ok = False
            continue

        if detect_disagreement(mcq, sol):
            entry["checks"].append({"mcq_index": i, "type": "disagreement", "detail": {"generated_answer": mcq.get("answer"), "solver": sol.get("chosen_answer")}})
            all_ok = False

        numeric_check, numeric_detail = numeric_consistency_check(qtext, sol_text)
        if numeric_check is False:
            entry["checks"].append({"mcq_index": i, "type": "numeric", "detail": numeric_detail})
            all_ok = False

        expl = sol.get("reason", "") if isinstance(sol, dict) else ""
        if detect_story_contradiction(qtext, expl):
            entry["checks"].append({"mcq_index": i, "type": "story_contradiction", "detail": "possible contradiction or missing entity in explanation"})
            all_ok = False

        if isinstance(val, dict) and val.get("valid") is False:
            entry["checks"].append({"mcq_index": i, "type": "validator", "detail": val.get("feedback", "")})
            all_ok = False

    entry["status"] = "pass" if all_ok and not hallu_reasons else "fail"
    if entry["status"] == "pass":
        summary["pass"] += 1
    else:
        summary["fail"] += 1

    results.append(entry)

report = {
    "run_at": datetime.utcnow().isoformat() + "Z",
    "uploaded_file": UPLOADED_FILE_URL,
    "summary": summary,
    "results": results
}

with open(RESULT_FILE, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("Stress test finished. Results saved to:", RESULT_FILE)
print("Summary:", summary)
