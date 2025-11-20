from agents.utils import call_llm

def generate_mcq(research_notes):
    prompt = f"""
    Based on the research notes below:

    {research_notes}

    Generate EXACTLY 3 MCQs in STRICT JSON format as a list:

    [
      {{
        "question": "",
        "options": ["A", "B", "C", "D"],
        "answer": "A",
        "explanation": ""
      }},
      {{
        "question": "",
        "options": ["A", "B", "C", "D"],
        "answer": "B",
        "explanation": ""
      }},
      {{
        "question": "",
        "options": ["A", "B", "C", "D"],
        "answer": "C",
        "explanation": ""
      }}
    ]

    Rules:
    - Respond ONLY with JSON.
    - Ensure the JSON is valid and parseable.
    - Do NOT include trailing commas.
    """

    return call_llm(prompt)
