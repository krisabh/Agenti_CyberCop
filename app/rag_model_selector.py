import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _expand_model_aliases(model_name: str) -> List[str]:
    """Return common alias forms for a model name (with/without `models/`)."""
    cleaned = model_name.strip()
    if not cleaned:
        return []

    aliases = [cleaned]
    if cleaned.startswith("models/"):
        aliases.append(cleaned.replace("models/", "", 1))
    else:
        aliases.append(f"models/{cleaned}")

    # Ordered unique
    seen = set()
    ordered: List[str] = []
    for alias in aliases:
        if alias and alias not in seen:
            seen.add(alias)
            ordered.append(alias)
    return ordered


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
        "embedding-001",
        "text-embedding-004",
    ]

    # Ordered unique, with alias expansion
    seen = set()
    ordered: List[str] = []
    for model_name in configured + defaults:
        for alias in _expand_model_aliases(model_name):
            if alias not in seen:
                seen.add(alias)
                ordered.append(alias)
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
                    supported.extend(_expand_model_aliases(name))

        # Ordered unique
        seen = set()
        ordered: List[str] = []
        for model_name in supported:
            if model_name not in seen:
                seen.add(model_name)
                ordered.append(model_name)
        return ordered
    except Exception:
        return []
