# app/extractor.py

import re

def extract_intelligence(messages):
    text = " ".join([m["text"] for m in messages])

    upi_ids = re.findall(r"\b[\w.-]+@[\w.-]+\b", text)
    phone_numbers = re.findall(r"\b\d{10}\b", text)
    urls = re.findall(r"https?://[^\s]+", text)

    return {
        "upiIds": list(set(upi_ids)),
        "phoneNumbers": list(set(phone_numbers)),
        "phishingLinks": list(set(urls))
    }
