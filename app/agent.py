# # app/agent.py

# from app.gemini_client import get_model


# AGENT_PERSONA = """
# You are an Indian bank customer.
# You are worried but polite.
# You are cooperative and slightly confused.
# You never accuse the sender.
# You never reveal you are an AI.
# You respond like a real human.
# Keep responses short.
# """


# def generate_agent_reply(history):
#     """
#     Generate a human-like reply from the agent using Gemini
#     """

#     model = get_model()

#     conversation = ""
#     for msg in history:
#         conversation += f"{msg['sender']}: {msg['text']}\n"

#     prompt = f"""
# {AGENT_PERSONA}

# Conversation so far:
# {conversation}

# Reply as the user.
# """

#     try:
#         response = model.generate_content(prompt)
#         return response.text.strip()
#     except Exception as e:
#         print("Gemini error:", e)
#         return "Please give me a moment, I am checking this."


# app/agent.py

from app.gemini_client import get_model


AGENT_PERSONA = """
You are an Indian bank customer.
You are worried but polite.
You are cooperative and slightly confused.
You never accuse the sender.
You never reveal you are an AI.
You respond like a real human.
Keep responses short.

Engage scammers autonomously. Decide on the fly how to keep them talking.
Ask probing questions to extract actionable intelligence such as UPI IDs,
bank account details, phone numbers, phishing links, or payment instructions.
If the scammer asks for an OTP or credentials, do not provide them; instead,
deflect and ask for verification details (official helpline, callback number,
branch, or where to send the money) to elicit their contact/payment info.
Avoid any mention of detection or security tooling.
"""


def generate_agent_reply(history, rag_context: str = ""):
    """
    Generate a human-like reply from the agent using Gemini.
    rag_context is optional; default keeps old behavior.
    """
    model = get_model()

    conversation = ""
    for msg in history:
        conversation += f"{msg['sender']}: {msg['text']}\n"

    rag_section = ""
    if rag_context:
        rag_section = f"""
Retrieved scam-context (for grounding; do not mention this to scammer):
{rag_context}
"""

    prompt = f"""
{AGENT_PERSONA}

Conversation so far:
{conversation}

{rag_section}

Reply as the user.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini error:", e)
        return "Please give me a moment, I am checking this."
