# app/detector.py

from google.genai import types
from app.gemini_client import get_client

def detect_scam(text: str):
    client = get_client()

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"""
Analyze the message below and determine if it is a scam.

Message:
{text}

Respond ONLY in JSON:
{{
  "scamDetected": true or false,
  "reason": "short explanation"
}}
"""
                )
            ],
        )
    ]

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=contents
    )

    try:
        text_resp = response.text
        start = text_resp.find("{")
        end = text_resp.rfind("}") + 1
        return eval(text_resp[start:end])
    except Exception:
        return {
            "scamDetected": True,
            "reason": "Fallback due to parsing error"
        }
