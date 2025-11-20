from agents.utils import call_llm

def validate_solution(mcq_json, solution_json):
    prompt = f"""
Validate the solution.
MCQ: {mcq_json}
Solution:{solution_json}
Return JSON:{{"valid":true,"feedback":""}}
"""
    return call_llm(prompt)
