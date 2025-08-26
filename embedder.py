from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from local_qdrant import get_qdrant_client, ensure_collection

def embed_and_upsert(docs, project_name: str, collection_name: str, qdrant_path: str, content_hash: str = None):
    """Embed documents and upsert them into Qdrant."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Initialize client directly
    client = get_qdrant_client(project_name)

    # Ensure collection exists before creating vectorstore
    ensure_collection(client, collection_name, embeddings)

    # Add content_hash to metadata if provided
    if content_hash:
        for doc in docs:
            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata['content_hash'] = content_hash

    # Initialize vectorstore
    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings,
    )

    # Upsert docs
    vectorstore.add_documents(docs)
    return len(docs)
