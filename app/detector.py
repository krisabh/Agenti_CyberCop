# # app/detector.py

# from app.gemini_client import get_model


# def detect_scam(text: str):
#     """
#     Detect whether a message is a scam using Gemini
#     """

#     model = get_model()

#     prompt = f"""
# Analyze the message below and determine if it is a scam.

# Message:
# {text}

# Respond ONLY in JSON:
# {{
#   "scamDetected": true or false,
#   "reason": "short explanation"
# }}
# """

#     response = model.generate_content(prompt)

#     try:
#         text_resp = response.text
#         start = text_resp.find("{")
#         end = text_resp.rfind("}") + 1
#         return eval(text_resp[start:end])
#     except Exception:
#         return {
#             "scamDetected": True,
#             "reason": "Fallback due to parsing error"
#         }


# app/detector.py
# app/detector.py
import json
import re
from textwrap import dedent

from pydantic import BaseModel, Field, ValidationError
from langchain_core.output_parsers import PydanticOutputParser

from app.gemini_client import get_model


class ScamDetectionResult(BaseModel):
    scamDetected: bool = Field(...)
    confidence: float = Field(...)
    reason: str = Field(...)


def detect_scam(text: str):
    """
    Detect whether a message is a scam using Gemini
    """

    model = get_model()

    prompt = dedent(
        f"""
        You are a scam detection classifier. Be conservative: only mark true when the
        message has explicit scam indicators. Examples include urgency or threats,
        credential/OTP requests, payment instructions (UPI IDs or account details),
        phishing links/URLs, impersonation of banks/government/brands, or fake rewards.
        If the message is normal or you are unsure, return false.

        Message:
        {text}

        Respond ONLY in JSON:
        {{
          "scamDetected": true or false,
          "confidence": 0.0-1.0,
          "reason": "short explanation"
        }}
        """
    ).strip()

    try:
        response = model.generate_content(prompt)
    except Exception:
        return {
            "scamDetected": False,
            "reason": "Model request failed"
        }

    text_resp = getattr(response, "text", "") or ""
    parser = PydanticOutputParser(pydantic_object=ScamDetectionResult)
    scam_detected = False
    confidence = 0.0
    reason = "Unable to parse model response"

    try:
        parsed = parser.parse(text_resp)
        scam_detected = bool(parsed.scamDetected)
        confidence = float(parsed.confidence)
        reason = parsed.reason
    except (ValidationError, ValueError):
        json_match = re.search(r"\{.*\}", text_resp, re.DOTALL)
        if not json_match:
            return {
                "scamDetected": False,
                "reason": "Unable to parse model response",
            }

        try:
            parsed_json = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return {
                "scamDetected": False,
                "reason": "Unable to parse model response",
            }

        scam_detected = bool(parsed_json.get("scamDetected", False))
        confidence = parsed_json.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        reason = parsed_json.get("reason", "No reason provided")

    if scam_detected and confidence < 0.6:
        scam_detected = False

    return {
        "scamDetected": scam_detected,
        "reason": reason,
    }
