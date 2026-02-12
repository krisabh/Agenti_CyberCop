import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from app.rag_model_selector import (
    discover_supported_embedding_models,
    parse_embedding_candidates,
)

try:
    from langchain_chroma import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError:  # pragma: no cover
    Chroma = None
    GoogleGenerativeAIEmbeddings = None


load_dotenv()

USE_RAG = os.getenv("USE_RAG", "false").lower() == "true"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "scam_knowledge")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "models/embedding-001")
RAG_EMBEDDING_MODELS = parse_embedding_candidates()
RAG_DEBUG = os.getenv("RAG_DEBUG", "false").lower() == "true"

_VECTORSTORE = None


def _get_vectorstore():
    global _VECTORSTORE

    if not USE_RAG or Chroma is None or GoogleGenerativeAIEmbeddings is None:
        return None

    if _VECTORSTORE is not None:
        return _VECTORSTORE

    discovered_models = discover_supported_embedding_models()
    candidate_models = RAG_EMBEDDING_MODELS + [
        model for model in discovered_models if model not in RAG_EMBEDDING_MODELS
    ]

    last_error = None
    for model_name in candidate_models:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
            # Validate model upfront to avoid runtime NOT_FOUND during retrieval.
            embeddings.embed_query("health-check")

            _VECTORSTORE = Chroma(
                collection_name=RAG_COLLECTION_NAME,
                embedding_function=embeddings,
                persist_directory=CHROMA_PERSIST_DIR,
            )
            print(f"RAG embedding model selected: {model_name}")
            return _VECTORSTORE
        except Exception as error:  # pragma: no cover
            last_error = error

    print("RAG embedding setup error:", last_error)
    print("RAG embedding candidates tried:", candidate_models)
    return None


def _build_query(history: List[Dict[str, Any]], latest_message: str) -> str:
    recent_history = history[-6:] if history else []
    rendered_turns = "\n".join(
        f"{item.get('sender', 'unknown')}: {item.get('text', '')}" for item in recent_history
    )
    return (
        "Find relevant scam tactics and safe probing guidance for this conversation.\n"
        f"Latest message: {latest_message}\n"
        f"Recent conversation:\n{rendered_turns}"
    )


def get_rag_context(
    history: List[Dict[str, Any]],
    latest_message: str,
    metadata: Dict[str, Any] | None = None,
) -> str:
    """Get retrieved context from vector DB.

    Returns empty string when disabled or unavailable, so base logic remains unchanged.
    """

    _ = metadata

    if not USE_RAG:
        if RAG_DEBUG:
            print("[RAG] USE_RAG=false, skipping retrieval")
        return ""

    try:
        vectorstore = _get_vectorstore()
        if vectorstore is None:
            if RAG_DEBUG:
                print("[RAG] Vectorstore unavailable, skipping retrieval")
            return ""

        query = _build_query(history, latest_message)
        docs = vectorstore.similarity_search(query, k=max(1, RAG_TOP_K))
        if RAG_DEBUG:
            print(f"[RAG] Query top_k={max(1, RAG_TOP_K)}, hits={len(docs)}")

        if not docs:
            if RAG_DEBUG:
                print("[RAG] No matching documents found")
            return ""

        sections = []
        for idx, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            category = doc.metadata.get("category", "general")
            sections.append(
                f"[Context {idx} | source={source} | category={category}]\n{doc.page_content.strip()}"
            )

        context = "\n\n".join(sections)
        if RAG_DEBUG:
            sources = [doc.metadata.get("source", "unknown") for doc in docs]
            print(f"[RAG] Sources used: {sources}")
            print(f"[RAG] Context length: {len(context)} chars")
        return context
    except Exception as error:
        print("RAG retrieval error:", error)
        if RAG_DEBUG:
            print("[RAG] Retrieval failed; returning empty context")
        return ""
