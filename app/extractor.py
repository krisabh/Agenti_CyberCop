# app/extractor.py

import re

SUSPICIOUS_KEYWORDS = {
    "bank",
    "otp",
    "link",
    "verify",
    "suspend",
    "suspended",
    "update",
    "upi",
    "phone",
    "account",
    "blocked",
    "urgent",
    "immediately",
    "password",
    "pin",
    "refund",
    "reward",
    "prize",
    "lottery",
    "kyc",
    "payment",
}


def extract_intelligence(messages):
    text = " ".join([m["text"] for m in messages])
    lowered = text.lower()

    upi_ids = re.findall(r"\b[\w.-]+@[\w.-]+\b", text)
    phone_numbers = re.findall(r"\b\d{10}\b", text)
    urls = re.findall(r"https?://[^\s]+", text)

    suspicious_keywords = sorted(
        {kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered}
    )

    return {
        "upiIds": list(set(upi_ids)),
        "phoneNumbers": list(set(phone_numbers)),
        "phishingLinks": list(set(urls)),
        "suspiciousKeywords": suspicious_keywords
    }
