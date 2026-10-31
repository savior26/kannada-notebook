from typing import Optional, Dict

from sqlalchemy.orm import Session

from myapp.database.models import Document, Notebook, OCRChunk
from myapp.vector_service.embeddings.embedding_service import create_query_embedding


def vector_search(
    db: Session,
    query: str,
    user_id,
    filter_parameter: Optional[Dict] = None,
    notebook_id=None,
):
    # --------------------------------
    # Stage 1: Query embedding
    # --------------------------------

    query_embedding = create_query_embedding(query)

    # --------------------------------
    # Stage 2: Filter Documents
    # --------------------------------

    document_query = (
        db.query(Document)
        .join(Notebook, Document.notebook_id == Notebook.id)
        .filter(
            Notebook.user_id == user_id
        )
    )
    if notebook_id is not None:
        document_query = document_query.filter(Notebook.id == notebook_id)

    # Filter by document_id if provided
    if filter_parameter:

        if "document_id" in filter_parameter:
            document_query = document_query.filter(
                Document.id == filter_parameter["document_id"]
            )
        if "document_ids" in filter_parameter:
            document_ids = filter_parameter["document_ids"]
            if not document_ids:
                return []
            document_query = document_query.filter(Document.id.in_(document_ids))

    documents = document_query.all()

    # If no documents belong to the user/filter
    if not documents:
        return []

    # Get document IDs
    document_ids = [
        document.id
        for document in documents
    ]

    # --------------------------------
    # Stage 3: Search OCRChunk
    # --------------------------------

    chunk_query = (
        db.query(OCRChunk)
        .filter(
            OCRChunk.document_id.in_(document_ids)
        )
    )

    # Filter by page number if provided
    if filter_parameter:

        if "page_number" in filter_parameter:
            chunk_query = chunk_query.filter(
                OCRChunk.page_number
                == filter_parameter["page_number"]
            )

    # --------------------------------
    # Stage 4: Vector similarity
    # --------------------------------

    chunks = (
        chunk_query
        .order_by(
            OCRChunk.embedding.cosine_distance(
                query_embedding
            )
        )
        .limit(5)
        .all()
    )


    return chunks
