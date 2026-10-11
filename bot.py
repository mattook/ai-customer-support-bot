import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_postgres import PGVector
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

CONNECTION_STRING = os.getenv("DATABASE_URL")
COLLECTION_NAME = "support_docs"


def run_rag_pipeline(customer_query: str) -> str:
    """
    Core RAG pipeline:
    1. Retrieves top chunks from pgvector.
    2. Evaluates context sufficiency using TypeSafe Jev.
    3. Escalates to human or generates response via Claude Haiku.
    """
    # 1. Retrieval
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PGVector(
        embeddings=embeddings,
        connection=CONNECTION_STRING,
        collection_name=COLLECTION_NAME,
        use_jsonb=True,
    )
    retrieved_docs = vector_store.similarity_search(customer_query, k=3)
    context_text = "\n\n---\n\n".join(
        [doc.page_content for doc in retrieved_docs])

    print(f"--- DEBUG ---")

    print(f"Query: {customer_query}")
    print(f"Retrieved Docs Count: {len(retrieved_docs)}")
    print(f"Context Length: {len(context_text)} chars")
    print(f"----------------")

    # 2. Jev Evaluation Gate
    with TypeSafeClient() as jev_client:
        questions = {
            "is_answer_present": Noul(
                instructions=(
                    "Does the provided documentation context contain enough explicit information "
                    "to answer the customer's question?"
                )
            )
        }
        jev_response = jev_client.system_one(
            state={"query": customer_query, "context": context_text},
            questions=questions
        )

    answer_probability = jev_response.nouls["is_answer_present"].noul

    # After your Jev block:
    print(f"--- JEV EVALUATION RESULT ---")
    print(f"Is Answer Present Value: {answer_probability}")
    print(f"Raw Jev Response: {jev_response}")
    print(f"-----------------------------")

    print(
        f"--- RETRIEVED TEXT PREVIEW ---\n{context_text}\n-----------------------------")

    # 3. Decision Branching
    if answer_probability < 0.85:
        return "🚨 [ESCALATE_TO_HUMAN]: The knowledge base lacks sufficient data to answer this query safely."

    # 4. Generation via Claude Haiku
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    system_prompt = (
        "You are an expert customer support assistant. "
        "Answer the customer's question strictly using only the provided documentation context."
    )

    response = llm.invoke(
        f"{system_prompt}\n\nContext:\n{context_text}\n\nQuestion:\n{customer_query}"
    )
    return response.content
