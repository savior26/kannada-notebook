from myapp.config.settings import settings
import requests

JINA_API_URL= settings.JINA_API_URL
JINA_MODEL = settings.JINA_MODEL
JINA_API_KEY = settings.JINA_API_KEY

def create_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using Jina AI Embedding API.

    The embedding model runs on Jina's servers,
    so Render does not need to load the model locally.
    """

    if not texts:
        return []

    response = requests.post(
        JINA_API_URL,
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": JINA_MODEL,
            "input": texts,
            "task": "retrieval.passage",
            "normalized": True,
            "embedding_type": "float",
            # IMPORTANT:
            # Only use this if your selected Jina model supports it.
            # "dimensions": 512,
        },
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    # Jina returns embeddings in the same order as the input.
    data = sorted(
        result["data"],
        key=lambda item: item["index"],
    )

    return [
        item["embedding"]
        for item in data
    ]



# ============================================================
# CREATE QUERY EMBEDDING
# ============================================================

def create_query_embedding(query: str) -> list[float]:

    if not JINA_API_KEY:
        raise RuntimeError(
            "JINA_API_KEY environment variable is not configured."
        )

    payload = {
        "model": JINA_MODEL,
        "input": [query],
        "task": "retrieval.query",
        "normalized": True,
        "embedding_type": "float",
    }

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        JINA_API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    return result["data"][0]["embedding"]

