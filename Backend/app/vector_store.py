"""Chroma vector store helper.

Provides helper functions to upsert/query documents inside
persistent Chroma collections shared by the backend.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv

from .embeddings import EmbeddingException, get_embedding

load_dotenv()

logger = logging.getLogger(__name__)
# Disable noisy chromadb telemetry by default in local dev; set env DISABLE_TELEMETRY=0 to enable
if os.getenv("DISABLE_TELEMETRY", "1") != "0":
    logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

try:
    import chromadb
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "chromadb is required for vector_store operations. Install via `pip install chromadb`."
    ) from exc

CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./data/chroma")
BATCH_SIZE = max(1, int(os.getenv("CHROMA_BATCH_SIZE", "16")))
os.makedirs(CHROMA_PERSIST_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)

_COLLECTION_NAMES = (
    "verified_claims",
    "news_articles",
    "gov_bulletins",
    "social_posts",
)

collections = {
    name: client.get_or_create_collection(name=name)
    for name in _COLLECTION_NAMES
}


def _chunk(items: Iterable[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """Yield small batches to keep sync times manageable."""
    batch: List[Dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def _get_collection(name: str):
    if name not in collections:
        raise ValueError(f"Unknown collection '{name}'. Valid: {list(collections)}")
    return collections[name]


def upsert_documents(collection: str, docs: List[Dict[str, Any]]) -> None:
    """Insert or update documents inside the selected collection."""
    if not docs:
        return

    chroma_collection = _get_collection(collection)

    for batch in _chunk(docs, BATCH_SIZE):
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        embeddings: List[List[float]] = []

        for doc in batch:
            try:
                doc_id = doc["id"]
                text = doc["text"]
                metadata = doc.get("metadata", {})
            except KeyError as exc:
                raise ValueError("Each document needs 'id' and 'text' fields") from exc

            ids.append(str(doc_id))
            documents.append(text)
            metadatas.append(metadata)

            try:
                embeddings.append(get_embedding(text))
            except EmbeddingException as exc:
                logger.error("Embedding failure for doc %s: %s", doc_id, exc)
                raise

        chroma_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )


def query_similar(collection: str, query_text: str, top_k: int = 5) -> Dict[str, Any]:
    """Return the raw Chroma query output for the provided text."""
    if not query_text:
        raise ValueError("query_text cannot be empty")

    chroma_collection = _get_collection(collection)
    embedding = get_embedding(query_text)

    return chroma_collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )


if __name__ == "__main__":  # Simple smoke test for local debugging
    sample_collection = "verified_claims"
    sample_doc = {
        "id": "demo-doc",
        "text": "Vaccines approved by WHO are effective and safe.",
        "metadata": {"source": "demo", "topic": "health"},
    }

    upsert_documents(sample_collection, [sample_doc])
    response = query_similar(sample_collection, "WHO approved vaccines", top_k=1)
    print(response)
