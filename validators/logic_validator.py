import json

def answer_matches(mcq_json, sol_json):
    try:
        mcq=json.loads(mcq_json)
        sol=json.loads(sol_json)
        return mcq["answer"]==sol["chosen_answer"]
    except:
        return False
