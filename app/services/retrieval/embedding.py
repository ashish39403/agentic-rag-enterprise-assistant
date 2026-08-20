import os
import time

import logfire
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

BATCH_SIZE = 50
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

_active_model = None
_embedding_dim = None


def _build_embedding_model() -> OpenAIEmbeddings:
    """
    Build the single embedding model used by ingestion and retrieval.

    Required env:
      OPENAI_API_KEY

    Optional env:
      OPENAI_BASE_URL
      OPENAI_EMBEDDING_MODEL
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or None

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file.")

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=api_key,
        base_url=base_url,
    )


def _init() -> None:
    """Initialize the embedding model once and probe its vector dimension."""
    global _active_model, _embedding_dim

    if _active_model is not None:
        return

    with logfire.span("Initialize embedding model", model=EMBEDDING_MODEL):
        model = _build_embedding_model()
        probe_vector = model.embed_query("probe")

        _active_model = model
        _embedding_dim = len(probe_vector)

        logfire.info(
            f"Embedding model ready: {EMBEDDING_MODEL} ({_embedding_dim}-dim)."
        )


def get_embedding_dim() -> int:
    """Return the active embedding dimension for Qdrant collection creation."""
    _init()
    return _embedding_dim


def embed_query(query: str) -> list[float]:
    """Embed one user/search query."""
    _init()
    return _active_model.embed_query(query)


def _embed_batch(batch: list[str]) -> list[list[float]]:
    """Embed one batch with simple retry for rate limits/transient API errors."""
    for attempt in range(4):
        try:
            return _active_model.embed_documents(batch)
        except Exception as e:
            err = str(e).lower()
            is_retryable = any(
                marker in err
                for marker in ("429", "rate", "quota", "timeout", "temporarily", "503")
            )

            if is_retryable and attempt < 3:
                wait = 2 ** attempt
                logfire.warning(
                    f"Embedding API retry in {wait}s "
                    f"(attempt {attempt + 1}/4): {e}"
                )
                time.sleep(wait)
                continue

            logfire.error(f"Embedding failed: {e}")
            raise

    raise RuntimeError("Embedding API failed after 4 attempts.")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed document chunks in batches."""
    _init()

    clean_texts = [text for text in texts if text and text.strip()]
    all_embeddings = []

    for i in range(0, len(clean_texts), BATCH_SIZE):
        batch = clean_texts[i : i + BATCH_SIZE]
        with logfire.span("Embed batch", model=EMBEDDING_MODEL, start=i, size=len(batch)):
            all_embeddings.extend(_embed_batch(batch))

    return all_embeddings
