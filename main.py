from orchestrator.orchestrator import run_system
from deployment.export_json import save_json

topic = input("Enter topic: ")
result = run_system(topic)
save_json(result)
print("Saved output to data/output/final_output.json")
