from app.gemini_client import get_model


SUMMARY_PROMPT = """
You summarize scammer behavior in a single concise sentence.
Focus on tactics used (urgency, threats, payment redirection, credential requests,
impersonation, phishing links). Avoid mentioning detection or analysis tools.
Return a single sentence only.
"""


def _extract_tactics(history: list) -> list[str]:
    scammer_text = " ".join(
        msg.get("text", "")
        for msg in history
        if msg.get("sender") == "scammer"
    ).lower()

    tactics = []
    if any(term in scammer_text for term in ["urgent", "immediately", "asap", "right away"]):
        tactics.append("urgency")
    if any(term in scammer_text for term in ["blocked", "suspended", "freeze", "deactivated"]):
        tactics.append("account threat")
    if any(term in scammer_text for term in ["upi", "transfer", "pay", "payment", "bank", "account","qr code","qr","code"]):
        tactics.append("payment redirection")
    if any(term in scammer_text for term in ["otp", "password", "pin", "cvv", "card"]):
        tactics.append("credential harvesting")
    if any(term in scammer_text for term in ["link", "http", "https", "c"]):
        tactics.append("phishing")

    return list(dict.fromkeys(tactics))

def _build_fallback_notes(history: list) -> str:
    tactics = _extract_tactics(history)
    if tactics:
        tactic_phrase = " and ".join(tactics)
        return f"Scammer used {tactic_phrase} tactics."

    return "Scammer engaged in suspicious messaging to solicit sensitive details."


def generate_agent_notes(history: list) -> str:
    if not history:
        return "Scammer engaged in suspicious messaging to solicit sensitive details."

    tactics = _extract_tactics(history)
    fallback_notes = _build_fallback_notes(history)

    conversation = ""
    for msg in history:
        sender = msg.get("sender", "unknown")
        text = msg.get("text", "")
        conversation += f"{sender}: {text}\n"

    prompt = f"""
{SUMMARY_PROMPT}

Conversation:
{conversation}

Return only the single-sentence summary.
"""

    try:
        model = get_model()
        response = model.generate_content(prompt)
        summary = response.text.strip().replace("\n", " ")
        tactic_phrase = " , ".join(tactics)
        if not summary:
            print("Agent Summary is empty")
            return fallback_notes
        if tactics:
            print(f"Tactics used by scammer {tactic_phrase}")
            return summary +' '+f"Tactics observed:{tactic_phrase}"
        return summary
    except Exception:
        return fallback_notes
 