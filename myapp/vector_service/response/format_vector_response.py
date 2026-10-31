def format_retrieved_documents(documents):

    context_parts = []

    for i, chunk in enumerate(documents, start=1):

        context_parts.append(
            f"""--- Source {i} ---
File: {chunk.document.filename}
Page: {chunk.page_number}
Chunk: {chunk.chunk_index}

{chunk.chunk_text}
"""
        )

    return "\n\n".join(context_parts)