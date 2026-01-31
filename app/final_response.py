from datetime import datetime


def build_final_api_response(
    scam_detected: bool,
    conversation_history: list,
    extracted_intelligence: dict,
    agent_notes: str
) -> dict:
    """
    Builds Point-8 compliant final API response
    """

    # --- Engagement Metrics ---
    if conversation_history:
        timestamps = [
            datetime.fromisoformat(
                msg["timestamp"].replace("Z", "+00:00")
            )
            for msg in conversation_history
        ]
        engagement_duration = int(
            (max(timestamps) - min(timestamps)).total_seconds()
        )
        total_messages = len(conversation_history) + 1
    else:
        engagement_duration = 0
        total_messages = 1

    # --- Final Response ---
    return {
        "status": "success",
        "scamDetected": scam_detected,
        "engagementMetrics": {
            "engagementDurationSeconds": engagement_duration,
            "totalMessagesExchanged": total_messages
        },
        "extractedIntelligence": {
            "bankAccounts": extracted_intelligence.get("bankAccounts", []),
            "upiIds": extracted_intelligence.get("upiIds", []),
            "phishingLinks": extracted_intelligence.get("phishingLinks", [])
        },
        "agentNotes": agent_notes
    }
