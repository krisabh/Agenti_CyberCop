import threading
import requests

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
_SESSION = requests.Session()


def send_final_result_to_guvi(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intelligence: dict,
    agent_notes: str
):
    """
    Sends mandatory final callback to GUVI (sync version).
    Use timeout=5 as per panel doc.
    """
    payload = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": extracted_intelligence.get("bankAccounts", []),
            "upiIds": extracted_intelligence.get("upiIds", []),
            "phishingLinks": extracted_intelligence.get("phishingLinks", []),
            "phoneNumbers": extracted_intelligence.get("phoneNumbers", []),
            "emailAddresses": extracted_intelligence.get("emailAddresses", []),
            "ifscCodes": extracted_intelligence.get("ifscCodes", []),
            "panNumbers": extracted_intelligence.get("panNumbers", []),
            "suspiciousKeywords": extracted_intelligence.get("suspiciousKeywords", []),
        },
        "agentNotes": agent_notes,
    }

    try:
        response = _SESSION.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=5,  # keep exactly as doc
        )
        print(f"[GUVI CALLBACK] status={response.status_code}")
        return response.status_code
    except Exception as error:
        print("GUVI callback failed:", str(error))
        return None


def send_final_result_to_guvi_async(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intelligence: dict,
    agent_notes: str
):
    """
    Fire-and-forget wrapper.
    """
    def _worker():
        try:
            send_final_result_to_guvi(
                session_id=session_id,
                scam_detected=scam_detected,
                total_messages=total_messages,
                extracted_intelligence=extracted_intelligence,
                agent_notes=agent_notes,
            )
        except Exception as error:
            print("GUVI callback worker error:", str(error))

    threading.Thread(target=_worker, daemon=True).start()
