from myapp.database.models import OCRChunk
from myapp.services.embeddings.embedding_service import create_embeddings

def save_chunks(
    db,
    document_id,
    chunks,
):
    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    embeddings = create_embeddings(texts)

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
        


    db.add_all(chunk_rows)
    db.commit()

    return chunk_rows