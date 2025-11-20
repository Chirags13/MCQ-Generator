import json

def is_valid_json(s):
    try:
        data=json.loads(s)
        req=["question","options","answer","explanation"]
        return all(k in data for k in req)
    except:
        return False
