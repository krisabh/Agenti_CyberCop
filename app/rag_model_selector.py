import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


def parse_embedding_candidates() -> List[str]:
    """Return embedding model candidates from env + safe defaults."""
    primary = os.getenv("RAG_EMBEDDING_MODEL", "models/embedding-001").strip()
    configured = [
        item.strip()
        for item in os.getenv("RAG_EMBEDDING_MODELS", "").split(",")
        if item.strip()
    ]

    defaults = [
        primary,
        "models/embedding-001",
        "models/text-embedding-004",
    ]

    # Ordered unique
    seen = set()
    ordered: List[str] = []
    for model_name in configured + defaults:
        if model_name not in seen:
            seen.add(model_name)
            ordered.append(model_name)
    return ordered


def discover_supported_embedding_models() -> List[str]:
    """Best-effort discovery of models supporting embedContent."""
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

        supported: List[str] = []
        for model in genai.list_models():
            methods = getattr(model, "supported_generation_methods", []) or []
            if "embedContent" in methods:
                name = getattr(model, "name", "")
                if name:
                    supported.append(name)
        return supported
    except Exception:
        return []
