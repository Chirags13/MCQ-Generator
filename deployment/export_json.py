import json, os

def save_json(data, filename="final_output1.json"):
    path = "data/output"
    os.makedirs(path, exist_ok=True)   # <-- creates folder if missing

    full_path = os.path.join(path, filename)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)

    print("Saved at:", full_path)
