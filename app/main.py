from typing import Optional
import os

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent import generate_agent_reply
from app.agent_notes import generate_agent_notes
from app.detector import detect_scam
from app.extractor import extract_intelligence
from app.guvi_callback import send_final_result_to_guvi
from app.memory import (
    add_message,
    get_final_result,
    get_message_count,
    get_messages,
    get_session,
    is_session_finalized,
    mark_scam_detected,
    mark_session_finalized,
    mark_takeover_accepted,
    set_final_result,
    was_scam_detected,
    was_takeover_accepted,
)
from app.rag import get_rag_context

load_dotenv()

API_KEY = os.getenv("API_KEY")
app = FastAPI(title="Agentic HoneyPot")
app.mount("/static", StaticFiles(directory="static"), name="static")


def _process_honeypot_payload(
    payload: Optional[dict],
    require_takeover_confirmation: bool = False,
):
    # GUVI endpoint tester case (no body)
    if not payload or payload == {}:
        return {
            "status": "success",
            "message": "Honeypot endpoint reachable"
        }

    session_id = payload["sessionId"]
    message = payload["message"]["text"]

    if not session_id or not message:
        return {
            "status": "success",
            "message": "Invalid payload format"
        }

    if is_session_finalized(session_id):
        return {
            "status": "success",
            "reply": "I am working on it.",
            "scamDetected": True,
            "sessionFinalized": True,
            "finalResult": get_final_result(session_id),
        }

    # 1) Store scammer message
    add_message(session_id, "scammer", message)

    # 2) Detect scam
    detection = detect_scam(message)
    if detection["scamDetected"]:
        mark_scam_detected(session_id)

    scam_detected = detection["scamDetected"] or was_scam_detected(session_id)

    history = []
    agent_reply = None
    extracted_intelligence = {}
    confirmation_required = False

    if scam_detected:
        history = get_messages(session_id)

        if require_takeover_confirmation and not was_takeover_accepted(session_id):
            confirmation_required = True
        else:
            # 3) Generate agent reply (RAG optional)
            rag_context = get_rag_context(
                history=history,
                latest_message=message,
                metadata=payload.get("metadata", {}),
            )
            agent_reply = generate_agent_reply(history, rag_context=rag_context)
            add_message(session_id, "agent", agent_reply)

            # 4) Extract intelligence
            extracted_intelligence = extract_intelligence(history)

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
                callback_result = send_final_result_to_guvi(
                    session_id=session_id,
                    scam_detected=True,
                    total_messages=total_messages,
                    extracted_intelligence=extracted_intelligence,
                    agent_notes=agent_notes
                )
                set_final_result(session_id, callback_result["payload"])
                mark_session_finalized(session_id)
                return {
                    "status": "success",
                    "reply": "I am working on it. Please wait...!",
                    "scamDetected": True,
                    "engagementComplete": True,
                    "finalResult": callback_result["payload"],
                }

    return {
        "status": "success",
        "reply": agent_reply or "",
        "scamDetected": scam_detected,
        "confirmationRequired": confirmation_required,
        "engagementComplete": bool(is_session_finalized(session_id)),
        "history": get_messages(session_id),
        "finalResult": get_final_result(session_id),
    }


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/chat")
def chat_page():
    return FileResponse("static/chat.html")


@app.get("/honeypot")
def honeypot_get(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "status": "success",
        "message": "Honeypot endpoint reachable"
    }


@app.post("/honeypot")
def honeypot(payload: Optional[dict] = Body(None), x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return _process_honeypot_payload(payload, require_takeover_confirmation=False)


@app.post("/ui/scammer-message")
def ui_scammer_message(payload: dict = Body(...)):
    return _process_honeypot_payload(payload, require_takeover_confirmation=True)


@app.post("/ui/user-message")
def ui_user_message(payload: dict = Body(...)):
    session_id = payload.get("sessionId")
    message = payload.get("text", "")

    if not session_id or not message.strip():
        raise HTTPException(status_code=400, detail="sessionId and text are required")

    add_message(session_id, "user", message.strip())
    return {
        "status": "success",
        "reply": "",
        "scamDetected": was_scam_detected(session_id),
        "history": get_messages(session_id),
        "engagementComplete": is_session_finalized(session_id),
        "finalResult": get_final_result(session_id),
    }


@app.post("/ui/takeover")
def ui_accept_takeover(payload: dict = Body(...)):
    session_id = payload.get("sessionId")
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required")

    mark_takeover_accepted(session_id)
    history = get_messages(session_id)
    if not history:
        return {"status": "success", "reply": "", "history": []}

    latest_message = history[-1].get("text", "")
    rag_context = get_rag_context(history=history, latest_message=latest_message, metadata={})
    agent_reply = generate_agent_reply(history, rag_context=rag_context)
    add_message(session_id, "agent", agent_reply)

    return {
        "status": "success",
        "reply": agent_reply,
        "history": get_messages(session_id),
        "scamDetected": True,
        "engagementComplete": is_session_finalized(session_id),
        "finalResult": get_final_result(session_id),
    }


@app.get("/ui/session/{session_id}")
def ui_get_session(session_id: str):
    session = get_session(session_id)
    return {
        "status": "success",
        "sessionId": session_id,
        "scamDetected": bool(session.get("scam_detected", False)),
        "takeoverAccepted": bool(session.get("takeover_accepted", False)),
        "engagementComplete": is_session_finalized(session_id),
        "history": session.get("messages", []),
        "finalResult": session.get("final_result"),
    }
