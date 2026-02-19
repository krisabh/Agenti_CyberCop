from fastapi import FastAPI, Header, HTTPException, Body
from dotenv import load_dotenv

from app.agent_notes import generate_agent_notes
import os
from typing import Any, Optional, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from app.memory import add_message, get_messages, get_message_count
from app.memory import was_scam_detected, mark_scam_detected
from app.detector import detect_scam
from app.agent import generate_agent_reply
from app.extractor import extract_intelligence
from app.guvi_callback import send_final_result_to_guvi_async
from app.memory import is_session_finalized, mark_session_finalized

load_dotenv()

API_KEY = os.getenv("API_KEY")
app = FastAPI()

# Latency budgets (seconds)
DETECT_TIMEOUT = float(os.getenv("DETECT_TIMEOUT_SECONDS", "28"))
REPLY_TIMEOUT = float(os.getenv("REPLY_TIMEOUT_SECONDS", "28"))

# Reuse worker pool to avoid thread startup overhead each request
_POOL = ThreadPoolExecutor(max_workers=8)

SCAM_HINTS = {
    "otp", "blocked", "suspended", "verify", "urgent", "immediately",
    "upi", "bank", "account", "link", "http://", "https://", "pin", "kyc"
}


def _extract_single_payload(obj: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], dict]:
    """
    Supports:
    1) Existing:
       {"sessionId":"...","message":{"text":"..."},"metadata":{...}}
    2) Panel:
       {"scenarioId":"...","initialMessage":"...","metadata":{...}}
    """
    metadata = obj.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    if "sessionId" in obj:
        session_id = obj.get("sessionId")
        msg = obj.get("message")
        if isinstance(msg, dict):
            message = msg.get("text")
        elif isinstance(msg, str):
            message = msg
        else:
            message = None
        return session_id, message, metadata

    if "scenarioId" in obj:
        session_id = obj.get("scenarioId")
        message = obj.get("initialMessage")
        if isinstance(message, dict):
            message = message.get("text")
        return session_id, message, metadata

    return None, None, metadata


def _normalize_request_payload(payload: Any) -> Tuple[Optional[str], Optional[str], dict]:
    # empty
    if payload is None:
        return None, None, {}

    # panel may send list of scenarios -> pick first valid
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


def _looks_like_scam_fast(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in SCAM_HINTS)


def _detect_scam_fast(message: str) -> bool:
    # fast pre-check first
    if _looks_like_scam_fast(message):
        return True

    # bounded model call
    future = _POOL.submit(detect_scam, message)
    try:
        result = future.result(timeout=DETECT_TIMEOUT)
        return bool(result.get("scamDetected"))
    except FuturesTimeoutError:
        future.cancel()
        return False
    except Exception:
        return False


def _generate_reply_fast(history: list) -> str:
    future = _POOL.submit(generate_agent_reply, history)
    try:
        out = future.result(timeout=REPLY_TIMEOUT)
        if isinstance(out, str) and out.strip():
            return out.strip()
        return "Please share your official helpline number and payment details again."
    except FuturesTimeoutError:
        future.cancel()
        return "I am checking this. Please share official number and where to verify."
    except Exception:
        return "Please share your official helpline number and where to verify this."


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/honeypot")
def honeypot_get(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"status": "success", "message": "Honeypot endpoint reachable"}


@app.post("/honeypot")
def honeypot(payload: Optional[Any] = Body(None), x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # tester / empty
    if payload is None or payload == {} or payload == []:
        return {"status": "success", "message": "Honeypot endpoint reachable"}

    session_id, message, _metadata = _normalize_request_payload(payload)

    if not session_id or not message:
        return {"status": "success", "message": "Invalid payload format"}

    if is_session_finalized(session_id):
        return {"status": "success", "reply": "I am working on it. "}

    # 1) Store scammer message
    add_message(session_id, "scammer", message)

    # 2) Fast scam detection
    if _detect_scam_fast(message):
        mark_scam_detected(session_id)

    scam_detected = was_scam_detected(session_id)

    history = []
    agent_reply = None
    extracted_intelligence = {}

    if scam_detected:
        history = get_messages(session_id)

        # 3) Fast bounded reply generation (NO RAG)
        agent_reply = _generate_reply_fast(history)
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

            # async callback -> do not block API response
            send_final_result_to_guvi_async(
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

    return {"status": "success", "reply": agent_reply or ""}
