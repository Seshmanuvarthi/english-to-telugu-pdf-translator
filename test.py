import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print("API Key:", api_key[:8] + "...")

# Configure with Gemini API
genai.configure(api_key=api_key)

try:
    # Correct model name (no "models/" prefix)
    model = genai.GenerativeModel('gemini-pro')

    # Send a prompt
    prompt = "Translate this to Telugu: The doctor advised him to rest for 3 days."
    response = model.generate_content(prompt)

    print("✅ Telugu Output:")
    print(response.text)

except Exception as e:
    print("❌ Error:", e)
