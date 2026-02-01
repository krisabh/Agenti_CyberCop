# app/main.py

from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv
from app.final_response import build_final_api_response

import os

from app.memory import add_message, get_messages, get_message_count
from app.detector import detect_scam
from app.agent import generate_agent_reply
from app.extractor import extract_intelligence
from app.guvi_callback import send_final_result_to_guvi
from app.memory import is_session_finalized, mark_session_finalized



load_dotenv()

API_KEY = os.getenv("API_KEY")
#GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/honeypot")
def honeypot(payload: dict, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_id = payload["sessionId"]
    message = payload["message"]["text"]

    if is_session_finalized(session_id):
        # Conversation lifecycle is over
        return {
            "status": "success",
            "scamDetected": True,
            "message": "Conversation completed. No further action required."
        }

    # 1️⃣ Store scammer message
    add_message(session_id, "scammer", message)

    # 2️⃣ Detect scam
    detection = detect_scam(message)

    agent_reply = None
    extracted_intelligence = {}

    if detection["scamDetected"]:
        history = get_messages(session_id)

        # 3️⃣ Generate agent reply
        agent_reply = generate_agent_reply(history)
        add_message(session_id, "agent", agent_reply)

        # 4️⃣ Extract intelligence
        extracted_intelligence = extract_intelligence(history)

        # ================================
        # 🔹 POINT 8 – FINAL API RESPONSE
        # ================================
        #engagement_complete = get_message_count(session_id) >= 6
        engagement_complete = (
                detection["scamDetected"] is True
                and extracted_intelligence is not None
                and any(extracted_intelligence.values())
        )
        if engagement_complete and not is_session_finalized(session_id):
            final_response = build_final_api_response(
                scam_detected=True,
                conversation_history=history,
                extracted_intelligence=extracted_intelligence,
                agent_notes="Scammer used urgency and payment redirection tactics"
            )
            # Mandatory GUVI callback
            send_final_result_to_guvi(
                session_id=session_id,
                scam_detected=True,
                total_messages=final_response["engagementMetrics"]["totalMessagesExchanged"],
                extracted_intelligence=extracted_intelligence,
                agent_notes=final_response["agentNotes"]
            )
            # Mark session as finalized
            mark_session_finalized(session_id)
            return final_response
        # ================================

    # 5️⃣ Default (ongoing conversation response)
    return {
        "status": "success",
        "scamDetected": detection["scamDetected"],
        "reason": detection["reason"],
        "agentReply": agent_reply,
        "totalMessages": get_message_count(session_id),
        #"extractedIntelligence": extracted_intelligence,
        "conversationHistory": history if detection["scamDetected"] else []
    }
