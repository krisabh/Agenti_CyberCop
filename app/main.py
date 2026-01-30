# app/main.py

from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv
import os
import time



from app.memory import add_message, get_messages, get_message_count
from app.detector import detect_scam
from app.agent import generate_agent_reply
from app.extractor import extract_intelligence

load_dotenv()

API_KEY = os.getenv("API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#genai.configure(api_key=GEMINI_API_KEY)
#model = genai.GenerativeModel("models/gemini-1.5-flash-001")


app = FastAPI()

@app.post("/honeypot")
def honeypot(payload: dict, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_id = payload["sessionId"]
    message = payload["message"]["text"]

    # Store scammer message
    add_message(session_id, "scammer", message)

    # Detect scam
    detection = detect_scam(message)

    agent_reply = None
    extracted_intelligence = {}

    if detection["scamDetected"]:
        history = get_messages(session_id)
        # agent_reply = generate_agent_reply(history, message)
        agent_reply = generate_agent_reply(history)

        #to check conversation history in server log
        print("=== CONVERSATION HISTORY ===")
        print(history)
        print("============================")
        # add_message(session_id, "user", agent_reply)
        add_message(session_id, "agent", agent_reply)

        # Extract intelligence after 4+ messages
        #if get_message_count(session_id) >= 4:
        extracted_intelligence = extract_intelligence(history)

    return {
        "status": "success",
        "scamDetected": detection["scamDetected"],
        "reason": detection["reason"],
        "agentReply": agent_reply,
        "totalMessages": get_message_count(session_id),
        "extractedIntelligence": extracted_intelligence,
        "conversation history": [history]
    }
