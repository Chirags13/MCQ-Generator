from agents.utils import call_llm

def generate_mcq(research_notes):
    prompt = f"""
Based on the notes:
{research_notes}
Generate FIVE MCQ in JSON:
{{
  "question":"",
  "options":["A","B","C","D"],
  "answer":"A",
  "explanation":""
}}
"""
    return call_llm(prompt)
