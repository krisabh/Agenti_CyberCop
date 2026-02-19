from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv

from app.agent_notes import generate_agent_notes
import os
from typing import Any, Optional
from fastapi import Body
from app.memory import add_message, get_messages, get_message_count
from app.memory import was_scam_detected, mark_scam_detected
from app.detector import detect_scam
from app.agent import generate_agent_reply
from app.extractor import extract_intelligence
from app.guvi_callback import send_final_result_to_guvi
from app.rag import get_rag_context
from app.memory import is_session_finalized, mark_session_finalized

load_dotenv()

API_KEY = os.getenv("API_KEY")
app = FastAPI()


def _normalize_request_payload(payload: Any) -> tuple[Optional[str], Optional[str], dict]:
    """Support both existing payload shape and panel scenario payload shape.

    Existing shape:
    {
      "sessionId": "...",
      "message": {"text": "..."},
      "metadata": {...}
    }

    Panel shape (single object or list with first object):
    {
      "scenarioId": "...",
      "initialMessage": "...",
      "metadata": {...}
    }
    """

    if isinstance(payload, list):
        if not payload:
            return None, None, {}
        payload = payload[0]

    if not isinstance(payload, dict):
        return None, None, {}

    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}

    # Existing request contract
    if "sessionId" in payload and isinstance(payload.get("message"), dict):
        session_id = payload.get("sessionId")
        message = payload.get("message", {}).get("text")
        return session_id, message, metadata

    # Panel-provided scenario contract
    if "scenarioId" in payload and "initialMessage" in payload:
        session_id = payload.get("scenarioId")
        message = payload.get("initialMessage")
        return session_id, message, metadata

    return None, None, metadata


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/honeypot")
def honeypot_get(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "status": "success",
        "message": "Honeypot endpoint reachable"
    }


@app.post("/honeypot")
def honeypot(payload: Optional[Any] = Body(None), x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # GUVI endpoint tester case (no body)
    if not payload or payload == {}:
        return {
            "status": "success",
            "message": "Honeypot endpoint reachable"
        }

    session_id, message, metadata = _normalize_request_payload(payload)

    if not session_id or not message:
        return {
            "status": "success",
            "message": "Invalid payload format"
        }

    if is_session_finalized(session_id):
        # Conversation lifecycle is over
        return {
            "status": "success",
            "reply": (
                "I am working on it. "
            ),
        }

    # 1) Store scammer message
    add_message(session_id, "scammer", message)

    # 2) Detect scam
    scam_detected = False
    detection = detect_scam(message)
    if detection["scamDetected"]:
        mark_scam_detected(session_id)

    scam_detected = detection["scamDetected"] or was_scam_detected(session_id)

    history = []
    agent_reply = None
    extracted_intelligence = {}

    if scam_detected:
        history = get_messages(session_id)

        # 3) Generate agent reply (RAG is optional; empty context when disabled/unavailable)
        rag_context = get_rag_context(
            history=history,
            latest_message=message,
            metadata=metadata,
        )
        agent_reply = generate_agent_reply(history, rag_context=rag_context)
        add_message(session_id, "agent", agent_reply)

        # 4) Extract intelligence
        extracted_intelligence = extract_intelligence(history)

        # Final callback condition (unchanged)

        # ================================
        # POINT 8 – FINAL API RESPONSE
        # ================================

        # new engagement_complete for suspicious keyword fix
        engagement_complete = (
            scam_detected is True
            and extracted_intelligence is not None
            and get_message_count(session_id) >= 17
            and any(
                value
                for key, value in extracted_intelligence.items()
                if key != "suspiciousKeywords"
            )
        )

        if engagement_complete and not is_session_finalized(session_id):
            agent_notes = generate_agent_notes(history)
            total_messages = get_message_count(session_id)
            # Mandatory GUVI callback
            send_final_result_to_guvi(
                session_id=session_id,
                scam_detected=True,
                total_messages=total_messages,
                extracted_intelligence=extracted_intelligence,
                agent_notes=agent_notes
            )
            # Mark session as finalized
            mark_session_finalized(session_id)
            return {
                "status": "success",
                "reply": (
                    "I am working on it. Please wait...!"
                ),
            }
        # ================================

    # 5 Default (ongoing conversation response)
    return {
        "status": "success",
        "reply": agent_reply or "",
    }
