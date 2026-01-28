# app/agent.py

from google.genai import types
from app.gemini_client import get_client

AGENT_PERSONA = """
You are an Indian bank customer.
You are worried but polite.
You are cooperative and slightly confused.
You never accuse the sender.
You never reveal you are an AI.
You respond like a real human.
Keep responses short.
"""

def generate_agent_reply(history, new_message):
    client = get_client()

    conversation = ""
    for msg in history:
        conversation += f"{msg['sender']}: {msg['text']}\n"

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"""
{AGENT_PERSONA}

Conversation so far:
{conversation}

Scammer says:
{new_message}

Reply as the user.
"""
                )
            ],
        )
    ]

    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=contents
    )

    return response.text.strip()
