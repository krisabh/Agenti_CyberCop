# # app/memory.py

# from datetime import datetime

# # In-memory session store
# _sessions = {}
# finalized_sessions = set()
# def get_session(session_id: str):
#     if session_id not in _sessions:
#         _sessions[session_id] = {
#             "messages": [],
#             "start_time": datetime.utcnow()
#         }
#     return _sessions[session_id]

# def add_message(session_id: str, sender: str, text: str):
#     session = get_session(session_id)
#     session["messages"].append({
#         "sender": sender,
#         "text": text,
#         "timestamp": datetime.utcnow().isoformat()
#     })

# def get_messages(session_id: str):
#     return get_session(session_id)["messages"]

# def get_message_count(session_id: str):
#     return len(get_session(session_id)["messages"])

# def is_session_finalized(session_id: str) -> bool:
#     return session_id in finalized_sessions


# def mark_session_finalized(session_id: str):
#     finalized_sessions.add(session_id)


# app/memory.py

from datetime import datetime

# In-memory session store
_sessions = {}
finalized_sessions = set()

def get_session(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = {
            "messages": [],
            "start_time": datetime.utcnow(),
            "scam_detected": False,
            "takeover_accepted": False,
            "final_result": None
        }
    return _sessions[session_id]

def add_message(session_id: str, sender: str, text: str):
    session = get_session(session_id)
    session["messages"].append({
        "sender": sender,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    })

def get_messages(session_id: str):
    return get_session(session_id)["messages"]

def get_message_count(session_id: str):
    return len(get_session(session_id)["messages"])

def was_scam_detected(session_id: str) -> bool:
    return bool(get_session(session_id).get("scam_detected", False))

def mark_scam_detected(session_id: str):
    session = get_session(session_id)
    session["scam_detected"] = True

def was_takeover_accepted(session_id: str) -> bool:
    return bool(get_session(session_id).get("takeover_accepted", False))

def mark_takeover_accepted(session_id: str):
    session = get_session(session_id)
    session["takeover_accepted"] = True

def set_final_result(session_id: str, final_result: dict):
    session = get_session(session_id)
    session["final_result"] = final_result

def get_final_result(session_id: str):
    return get_session(session_id).get("final_result")

def is_session_finalized(session_id: str) -> bool:
    return session_id in finalized_sessions

def mark_session_finalized(session_id: str):
    finalized_sessions.add(session_id)
