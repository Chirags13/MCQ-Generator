from agents.utils import call_llm

def research_topic(topic):
    prompt = f"Research the topic '{topic}' in 6 bullet points. Output plain text."
    return call_llm(prompt)
