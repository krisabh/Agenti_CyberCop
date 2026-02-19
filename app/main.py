from fastapi import FastAPI, Header, HTTPException, Body
from dotenv import load_dotenv

from app.agent_notes import generate_agent_notes
import os
from typing import Any, Optional, Tuple, Dict

from app.memory import add_message, get_messages, get_message_count
from app.memory import was_scam_detected, mark_scam_detected
from app.detector import detect_scam
from app.agent import generate_agent_reply
from app.extractor import extract_intelligence
from app.guvi_callback import send_final_result_to_guvi
from app.memory import is_session_finalized, mark_session_finalized

load_dotenv()

API_KEY = os.getenv("API_KEY")
app = FastAPI()


def _extract_single_payload(obj: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], dict]:
    """
    Supports:
    1) Existing:
       {
         "sessionId": "...",
         "message": {"text": "..."},
         "metadata": {...}
       }

    2) New panel:
       {
         "scenarioId": "...",
         "initialMessage": "...",
         "metadata": {...}
       }
    """
    metadata = obj.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    # Existing contract
    if "sessionId" in obj:
        session_id = obj.get("sessionId")
        message_obj = obj.get("message")
        if isinstance(message_obj, dict):
            message = message_obj.get("text")
        elif isinstance(message_obj, str):
            message = message_obj
        else:
            message = None
        return session_id, message, metadata

    # New panel contract
    if "scenarioId" in obj:
        session_id = obj.get("scenarioId")
        message = obj.get("initialMessage")
        if isinstance(message, dict):
            message = message.get("text")
        return session_id, message, metadata

    return None, None, metadata


def _normalize_request_payload(payload: Any) -> Tuple[Optional[str], Optional[str], dict]:
    """
    Handles dict OR list payload.
    For list payloads, picks first valid item.
    """
    if payload is None:
        return None, None, {}

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                session_id, message, metadata = _extract_single_payload(item)
                if session_id and message:
                    return session_id, message, metadata
        return None, None, {}

    if isinstance(payload, dict):
        return _extract_single_payload(payload)

    return None, None, {}


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

    # endpoint tester / empty body
    if payload is None or payload == {} or payload == []:
        return {
            "status": "success",
            "message": "Honeypot endpoint reachable"
        }

    session_id, message, _metadata = _normalize_request_payload(payload)

    if not session_id or not message:
        return {
            "status": "success",
            "message": "Invalid payload format"
        }

    if is_session_finalized(session_id):
        return {
            "status": "success",
            "reply": "I am working on it. ",
        }

    # 1) Store scammer message
    add_message(session_id, "scammer", message)

    # 2) Detect scam
    detection = detect_scam(message)
    if detection.get("scamDetected"):
        mark_scam_detected(session_id)

    scam_detected = bool(detection.get("scamDetected")) or was_scam_detected(session_id)

    history = []
    agent_reply = None
    extracted_intelligence = {}

    if scam_detected:
        history = get_messages(session_id)

        # 3) Generate agent reply (NO RAG)
        agent_reply = generate_agent_reply(history)
        add_message(session_id, "agent", agent_reply)

        # 4) Extract intelligence
        extracted_intelligence = extract_intelligence(history)

        # final callback condition (same logic)
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

            send_final_result_to_guvi(
                session_id=session_id,
                scam_detected=True,
                total_messages=total_messages,
                extracted_intelligence=extracted_intelligence,
                agent_notes=agent_notes
            )

            mark_session_finalized(session_id)
            return {
                "status": "success",
                "reply": "I am working on it. Please wait...!",
            }

    # ongoing conversation response
    return {
        "status": "success",
        "reply": agent_reply or "",
    }
