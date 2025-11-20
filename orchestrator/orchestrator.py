import json
from agents.researcher import research_topic
from agents.generator import generate_mcq
from agents.solver import solve_mcq
from agents.validator import validate_solution
from validators.schema_validator import is_valid_json
from validators.logic_validator import answer_matches
from deployment.export_json import save_json
from config import MAX_RETRIES

def run_system(topic):
    print("\n=== Starting Multi-Agent MCQ Pipeline ===\n")

    # Step 1 — Research
    print("[1] Researching topic...")
    research_notes = research_topic(topic)

    # Step 2 — Generate 3 MCQs
    print("[2] Generating MCQs...")
    raw_mcq_list = generate_mcq(research_notes)

    # Parse raw JSON
    try:
        mcq_list = json.loads(raw_mcq_list)
    except:
        print("[ERROR] MCQ generator returned invalid JSON.")
        return {"error": "MCQ JSON invalid"}

    if not isinstance(mcq_list, list) or len(mcq_list) != 3:
        print("[ERROR] MCQ generator did not return exactly 3 MCQs.")
        return {"error": "MCQ list size incorrect"}

    final_mcqs = []
    final_solutions = []
    final_validations = []

    # Step 3 — Process each MCQ one by one
    for i, mcq in enumerate(mcq_list):
        print(f"\n=== Processing MCQ {i+1} of 3 ===")

        mcq_json = json.dumps(mcq)

        # Validate schema
        if not is_valid_json(mcq_json):
            print("[ERROR] MCQ schema invalid, skipping...")
            final_mcqs.append(mcq)
            final_solutions.append({"error": "invalid mcq"})
            final_validations.append({"valid": False, "feedback": "MCQ invalid"})
            continue

        # Solve
        print("→ Solving MCQ...")
        solution_raw = solve_mcq(mcq_json)

        try:
            solution = json.loads(solution_raw)
        except:
            print("[ERROR] Solution JSON invalid")
            solution = {"error": "invalid solution"}

        # Validate solution against answer
        print("→ Validating solution...")
        correct = answer_matches(mcq_json, solution_raw)

        validation_raw = validate_solution(mcq_json, solution_raw)
        try:
            validation = json.loads(validation_raw)
        except:
            validation = {"valid": False, "feedback": "validator JSON invalid"}

        # Store results
        final_mcqs.append(mcq)
        final_solutions.append(solution)
        final_validations.append(validation)

    # Step 4 — Build final structure
    final_output = {
        "topic": topic,
        "research_notes": research_notes,
        "mcqs": final_mcqs,
        "solutions": final_solutions,
        "validations": final_validations
    }

    # Step 5 — Export final JSON
    save_json(final_output)

    print("\n=== Pipeline Complete! ===")
    return final_output
