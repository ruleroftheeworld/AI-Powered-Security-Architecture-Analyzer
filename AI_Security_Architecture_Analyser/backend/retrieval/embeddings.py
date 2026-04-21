import threading
from sentence_transformers import SentenceTransformer
from typing import Optional

MODEL_NAME = "intfloat/e5-small-v2"

class _EmbeddingModel:
    _instance: Optional["SentenceTransformer"] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> SentenceTransformer:
        """Lazy singleton loading with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = SentenceTransformer(MODEL_NAME)
        return cls._instance

def embed_query(text: str) -> list[float]:
    """Embed a user query (uses 'query:' prefix per e5 best practices)."""
    if not text or not text.strip():
        return []
    model = _EmbeddingModel.get_instance()
    query_text = f"query: {text.strip()}"
    return model.encode(
        query_text,
        convert_to_tensor=False,
        normalize_embeddings=True,
    ).tolist()

def embed_document(text: str) -> list[float]:
    """Embed a guidance document (uses 'passage:' prefix per e5 best practices)."""
    if not text or not text.strip():
        return []
    model = _EmbeddingModel.get_instance()
    doc_text = f"passage: {text.strip()}"
    return model.encode(
        doc_text,
        convert_to_tensor=False,
        normalize_embeddings=True,
    ).tolist()