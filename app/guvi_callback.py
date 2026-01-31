import requests


GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"


def send_final_result_to_guvi(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intelligence: dict,
    agent_notes: str
):
    """
    Sends mandatory final callback to GUVI (Point 12)
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
            "suspiciousKeywords": extracted_intelligence.get("suspiciousKeywords", [])
        },
        "agentNotes": agent_notes
    }

    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=5
        )
        print("GUVI callback status:", response.status_code)
        return response.status_code
    except Exception as e:
        print("GUVI callback failed:", str(e))
        return None
