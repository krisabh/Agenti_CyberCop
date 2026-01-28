# app/memory.py

from datetime import datetime

# In-memory session store
_sessions = {}

def get_session(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = {
            "messages": [],
            "start_time": datetime.utcnow()
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
