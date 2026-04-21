import json
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from .guidance_schema import GuidanceSnippet
from .embeddings import embed_query, embed_document

BASE_DIR = Path(__file__).parent.parent
GUIDANCE_JSON = BASE_DIR / "data" / "security_guidance.json"
CHROMA_PERSIST_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "security_guidance"

def get_collection() -> chromadb.Collection:
    """Return (or create) the single persistent collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # normalized embeddings
    )
    return collection

def index_guidance() -> None:
    """Deterministic indexing – always up-to-date via upsert."""
    if not GUIDANCE_JSON.exists():
        raise FileNotFoundError(f"Guidance file not found at {GUIDANCE_JSON}")

    with open(GUIDANCE_JSON, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    snippets: List[GuidanceSnippet] = [GuidanceSnippet.model_validate(item) for item in raw_data]

    snippets = sorted(snippets,key = lambda x: x.id)

    collection = get_collection()

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    embeddings: List[List[float]] = []

    for snippet in snippets:
        ids.append(snippet.id)

        # Rich, self-contained document for both storage and embedding
        doc_text = (
            f"Category: {snippet.category}\n"
            f"Title: {snippet.title}\n"
            f"Description: {snippet.description}\n"
            f"Mitigation: {snippet.mitigation or 'N/A'}\n"
            f"Tags: {', '.join(snippet.tags)}\n"
            f"Source: {snippet.source} {snippet.control or ''}"
        )

        documents.append(doc_text)
        metadatas.append({
            "source": snippet.source,
            "control": snippet.control,
            "category": snippet.category,
            "cwe": snippet.cwe,
            "severity": snippet.severity,
            "tags": snippet.tags,          
        })
        embeddings.append(embed_document(doc_text))

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f"Indexed {len(snippets)} guidance snippets (deterministic upsert).")

def retrieve_guidance(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve top-k guidance with optional metadata filtering."""
    if not query or not query.strip():
        return []

    collection = get_collection()
    query_emb = embed_query(query)

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        where=filters,                    # e.g. {"category": "Authentication"} or {"severity": "High"}
        include=["metadatas", "documents", "distances"],
    )

    retrieved: List[Dict[str, Any]] = []
    for i in range(len(results["ids"][0])):
        retrieved.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return retrieved