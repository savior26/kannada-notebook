from langchain_huggingface import HuggingFaceEmbeddings


embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-base"
)


def create_embeddings(texts: list[str]):
    return embedding_model.embed_documents(texts)


def create_query_embedding(query: str):
    return embedding_model.embed_query(query)