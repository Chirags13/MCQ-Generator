from google import genai
import time
from config import GEMINI_API_KEY, MODEL

client = genai.Client(api_key=GEMINI_API_KEY)

def call_llm(prompt: str, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            )
            return response.text

        except Exception as e:
            print(f"[Retry {attempt+1}/{max_retries}] Gemini Error:", e)
            if attempt == max_retries - 1:
                raise
            time.sleep(2 + attempt)  # exponential backoff
