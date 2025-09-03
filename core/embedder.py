from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from core.vector_store import get_qdrant_client, ensure_collection

def embed_documents(docs, project_name: str, collection_name: str):
    """Embed documents and add them to the vector store."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Get Qdrant client for the project
    client = get_qdrant_client(project_name)

    # Ensure collection exists
    ensure_collection(client, collection_name, embeddings)

    # Create vectorstore and add documents
    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings,
    )

    # Add documents to vector store
    vectorstore.add_documents(docs)
    return len(docs)
