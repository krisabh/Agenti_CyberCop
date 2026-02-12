import os
from pathlib import Path

from dotenv import load_dotenv

from app.rag_model_selector import (
    discover_supported_embedding_models,
    parse_embedding_candidates,
)

try:
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as error:  # pragma: no cover
    raise RuntimeError(
        "RAG dependencies are missing. Run: pip install -r requirements.txt"
    ) from error


load_dotenv()

KNOWLEDGE_DIR = Path(os.getenv("RAG_KNOWLEDGE_DIR", "./knowledge"))
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "scam_knowledge")
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "models/embedding-001")
RAG_EMBEDDING_MODELS = parse_embedding_candidates()
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
RAG_DEBUG = os.getenv("RAG_DEBUG", "false").lower() == "true"


def _category_for_file(file_path: Path) -> str:
    if file_path.parent == KNOWLEDGE_DIR:
        return "general"
    return file_path.parent.name


def load_documents() -> list[Document]:
    files = list(KNOWLEDGE_DIR.rglob("*.md")) + list(KNOWLEDGE_DIR.rglob("*.txt"))
    documents: list[Document] = []

    for file_path in files:
        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            continue

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "category": _category_for_file(file_path),
                },
            )
        )

    return documents


def ingest() -> None:
    if not KNOWLEDGE_DIR.exists():
        raise RuntimeError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    documents = load_documents()
    if RAG_DEBUG:
        print(f"[RAG_INGEST] Knowledge directory: {KNOWLEDGE_DIR}")

    if not documents:
        raise RuntimeError("No .md/.txt files found in knowledge directory.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)

    if RAG_DEBUG:
        sources = sorted({doc.metadata.get("source", "unknown") for doc in documents})
        print(f"[RAG_INGEST] Source files loaded ({len(sources)}):")
        for src in sources:
            print(f"  - {src}")

    discovered_models = discover_supported_embedding_models()
    candidate_models = RAG_EMBEDDING_MODELS + [
        model for model in discovered_models if model not in RAG_EMBEDDING_MODELS
    ]

    last_error = None
    for model_name in candidate_models:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
            vectorstore = Chroma(
                collection_name=RAG_COLLECTION_NAME,
                embedding_function=embeddings,
                persist_directory=CHROMA_PERSIST_DIR,
            )
            vectorstore.add_documents(chunks)
            print(f"Embedding model used: {model_name}")
            break
        except Exception as error:
            last_error = error
    else:
        raise RuntimeError(
            "Failed to ingest documents with all embedding model candidates. "
            "Check .env format (KEY=value), then set RAG_EMBEDDING_MODELS to a valid "
            "embed model from your project (you can list via google.generativeai.list_models())."
        ) from last_error

    print(f"Model candidates tried: {candidate_models}")
    if RAG_DEBUG:
        print(f"[RAG_INGEST] Chunk size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    print(f"Ingested {len(documents)} files as {len(chunks)} chunks.")
    print(f"Collection: {RAG_COLLECTION_NAME}")
    print(f"Persist directory: {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    ingest()
