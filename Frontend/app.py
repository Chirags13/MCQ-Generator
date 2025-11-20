from flask import Flask, render_template, request
import json
import sys
import os

# Ensure backend modules can be imported
sys.path.append("..")

from orchestrator.orchestrator import run_system

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form.get("topic")
        result = run_system(topic)

        # Convert dict to readable JSON for frontend
        mcqs = result.get("mcqs", [])
        research = result.get("research_notes", "")

        return render_template("index.html", topic=topic, research=research, mcqs=mcqs)

    return render_template("index.html", topic=None, research=None, mcqs=None)


if __name__ == "__main__":
    app.run(debug=True)
