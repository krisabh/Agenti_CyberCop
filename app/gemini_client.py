# app/gemini_client.py

import os
from google import genai

def get_client():
    return genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY")
    )
