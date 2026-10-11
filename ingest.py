import os
from dotenv import load_dotenv
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from bs4 import BeautifulSoup

load_dotenv()

CONNECTION_STRING = os.getenv("DATABASE_URL")
COLLECTION_NAME = "support_docs"
DOCS_URL = os.getenv("SCRAPE_URL")


def load_and_chunk_web_docs(root_url: str, max_depth: int = 3):
    """
    Scrapes the entire documentation site recursively starting from the root,
    stripping navigation noise and extracting core content.
    """
    def clean_html(html):
        soup = BeautifulSoup(html, "html.parser")

        # Remove layout clutter that ruins RAG chunks
        for element in soup(["nav", "aside", "footer", "header", "script", "style", "form"]):
            element.decompose()

        # Target standard documentation body containers if present
        main_content = soup.find("main") or soup.find("article") or soup.find(
            "div", class_=["content", "markdown", "doc-content", "theme-doc-markdown"])

        if main_content:
            return main_content.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    print(f"Crawling documentation root: {root_url} (Max Depth: {max_depth})")
    loader = RecursiveUrlLoader(
        url=root_url,
        max_depth=max_depth,
        extractor=clean_html
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} clean document pages.")

    # Split text into bite-sized chunks ideal for semantic search
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    chunked_docs = text_splitter.split_documents(docs)
    print(f"Split into {len(chunked_docs)} total optimized chunks.")

    return chunked_docs


def store_docs_in_pgvector(chunked_docs):
    """
    Generates OpenAI embeddings and saves them into PostgreSQL pgvector.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = PGVector.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        connection=CONNECTION_STRING,
        collection_name=COLLECTION_NAME,
        use_jsonb=True,
        pre_delete_collection=True,  # Wipes old polluted chunks automatically on re-run
    )

    print(
        f"Successfully stored {len(chunked_docs)} chunks into pgvector collection '{COLLECTION_NAME}'.")
    return vector_store


if __name__ == "__main__":
    # Point directly to the root docs directory
    root_docs_url = DOCS_URL

    chunks = load_and_chunk_web_docs(root_docs_url, max_depth=3)
    db = store_docs_in_pgvector(chunks)
