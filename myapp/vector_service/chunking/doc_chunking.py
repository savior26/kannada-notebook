from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def create_docs_from_pages_extracted_by_ocr(pages, filename):
    documents = []

    for page in pages:
        document = Document(
            page_content=page.raw_text,
            metadata={
                "page_number": page.page_number
            }
        )

        documents.append(document)

    return documents


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=[
        "\n\n",   # paragraph
        "\n",    # line
        " ",     # word boundary
        "",      # individual characters as final fallback
    ],
    length_function=len
)

def create_chunks(documents):
    chunks = []

    for document in documents:

        document_chunks = text_splitter.split_documents([document])

        for i, chunk in enumerate(document_chunks):

            chunk.metadata["chunk_id"] = i
            chunk.metadata["total_chunks"] = len(document_chunks)

            chunks.append(chunk)

    return chunks
