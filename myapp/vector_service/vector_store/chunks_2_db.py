import logging
from time import perf_counter

from myapp.database.models import OCRChunk
from myapp.vector_service.embeddings.embedding_service import create_embeddings

logger = logging.getLogger(__name__)

def save_chunks(
    db,
    document_id,
    chunks,
):
    if not chunks:
        return []

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    embedding_started = perf_counter()
    embeddings = create_embeddings(texts)
    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Embedding service returned {len(embeddings)} vectors for {len(chunks)} chunks"
        )

    expected_dimensions = OCRChunk.__table__.c.embedding.type.dim
    invalid_dimensions = sorted(
        {len(embedding) for embedding in embeddings if len(embedding) != expected_dimensions}
    )
    if invalid_dimensions:
        raise ValueError(
            f"Embedding service returned vector dimensions {invalid_dimensions}; "
            f"database expects {expected_dimensions}"
        )
    logger.info(
        "Generated embeddings for %s chunk(s) in %.2f seconds",
        len(texts),
        perf_counter() - embedding_started,
    )

    chunk_rows = []

    for chunk, embedding in zip(chunks, embeddings):

        chunk_row = OCRChunk(
            document_id=document_id,
            page_number=chunk.metadata["page_number"],
            chunk_index=chunk.metadata["chunk_id"],
            chunk_text=chunk.page_content,
            total_chunks=chunk.metadata['total_chunks'],
            embedding=embedding
        )
        
        chunk_rows.append(chunk_row)
        
    database_started = perf_counter()
    db.add_all(chunk_rows)
    db.commit()
    logger.info(
        "Stored %s chunk row(s) in %.2f seconds",
        len(chunk_rows),
        perf_counter() - database_started,
    )

    return chunk_rows
