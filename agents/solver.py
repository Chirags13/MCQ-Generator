from agents.utils import call_llm

def solve_mcq(mcq_json):
    prompt = f"""
Solve this MCQ:
{mcq_json}
Return JSON: {{"chosen_answer":"A","reason":""}}
"""
    return call_llm(prompt)
