# # app/extractor.py

# import re

# SUSPICIOUS_KEYWORDS = {
#     "bank",
#     "otp",
#     "link",
#     "verify",
#     "suspend",
#     "suspended",
#     "update",
#     "upi",
#     "phone",
#     "account",
#     "blocked",
#     "urgent",
#     "immediately",
#     "password",
#     "pin",
#     "refund",
#     "reward",
#     "prize",
#     "lottery",
#     "kyc",
#     "payment",
# }


# def extract_intelligence(messages):
#     text = " ".join([m["text"] for m in messages])
#     lowered = text.lower()

#     upi_ids = re.findall(r"\b[\w.-]+@[\w.-]+\b", text)
#     phone_numbers = re.findall(r"\b\d{10}\b", text)
#     urls = re.findall(r"https?://[^\s]+", text)

#     suspicious_keywords = sorted(
#         {kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered}
#     )

#     return {
#         "upiIds": list(set(upi_ids)),
#         "phoneNumbers": list(set(phone_numbers)),
#         "phishingLinks": list(set(urls)),
#         "suspiciousKeywords": suspicious_keywords
#     }


# app/extractor.py

import re

SUSPICIOUS_KEYWORDS = {
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
     "qr code",
     "download"
 }
 
 
def extract_intelligence(messages):
     text = " ".join([m["text"] for m in messages])
     lowered = text.lower()
     upi_matches = re.findall(r"\b[\w.-]+@[\w.-]+\b", text)
     phone_numbers = re.findall(r"\b(?:\+91)?\d{10}\b", text)
     urls = re.findall(r"https?://[^\s]+", text)
     email_pattern = re.compile(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com\b"
     )
     emails = email_pattern.findall(text)
    #  ifsc_codes = re.findall(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", text)
     pan_numbers = re.findall(r"\b[A-Z]{5}\d{4}[A-Z]\b", text)
     labeled_accounts = re.findall(
        r"\b(?:account(?: number)?|acct|acc(?:ount)?|a/c)\s*[:\-]?\s*(\d{6,18})\b",
        text,
        flags=re.IGNORECASE
    )
     bank_accounts = set(labeled_accounts)
     upi_ids = [
        upi for upi in upi_matches if not email_pattern.fullmatch(upi)
    ]

     suspicious_keywords = sorted(
        {kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered}
     )
 
     return {
        "bankAccounts": sorted(bank_accounts),
        "upiIds": sorted(set(upi_ids)),
        "phoneNumbers": list(set(phone_numbers)),
        "phishingLinks": list(set(urls)),
        "emailAddresses": sorted(set(emails)),
        # "ifscCodes": sorted(set(ifsc_codes)),
        "panNumbers": sorted(set(pan_numbers)),
        "suspiciousKeywords": suspicious_keywords
     }
