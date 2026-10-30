from myapp.config.llm import ai_Model
from myapp.services.response.format_vector_response import format_retrieved_documents

from myapp.services.search.vector_search import vector_search


def answer_question(
    db,
    query,
    user_id,
    filter_parameter=None,
    notebook_id=None,
    response_language="en",
):

    documents = vector_search(
        db=db,
        query=query,
        user_id=user_id,
        filter_parameter=filter_parameter,
        notebook_id=notebook_id,
    )

    context = format_retrieved_documents(documents)

    language_instruction = {
        "en": "Answer in English.",
        "hi": "Answer in Hindi.",
        "kn": "Answer in Kannada.",
    }.get(response_language, "Answer in English.")

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the information
provided in the retrieved context.

If the answer cannot be found in the context, say:

"I could not find the answer in the provided documents."

Do not invent information.
{language_instruction}
If the answer is not in the context, clearly say that in the requested language.

Retrieved Context:

{context}

User Question:

{query}

Answer:
"""

    response = ai_Model.invoke(prompt)

    return response.content
