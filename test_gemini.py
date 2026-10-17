import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("Gemini API key is missing.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Introduce yourself as the AI assistant for LifePilot-AI in two sentences."
)

print("\n===== LifePilot-AI Gemini Test =====")
print(response.text)