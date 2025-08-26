import os
from dotenv import load_dotenv

load_dotenv()

import os
from pathlib import Path
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from tqdm import tqdm
from qdrant_client.models import VectorParams, Distance

from text_parsers.unified_parser import parse_file
from db import *
import streamlit as st

# --- Settings ---
BATCH_SIZE = 12                          # tune for performance

@st.cache_resource
def get_qdrant_client(project_name: str):
    """
    Return a QdrantClient for the given project.
    Stores data under: projects/{project_name}/qdrant
    """
    project_dir = Path("projects") / project_name
    qdrant_path = project_dir / "qdrant"
    qdrant_path.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(qdrant_path))


# --- Step 1: Recursively find all .txt files ---
from langchain.schema import Document

def find_txt_files(root_dir: str) -> list[Path]:
    return [p for p in Path(root_dir).rglob('*.txt')]

# --- Step 2: Load ONE file and attach metadata ---
def load_one_document(path: Path, root_dir: str):
    parsed = parse_file(str(path))  # unified output
    return [Document(page_content=parsed["page_content"], metadata=parsed["metadata"])]

# --- Step 3: Chunk helper ---
def adaptive_chunk_documents(docs: list[Document], model: str = 'text-embedding-3-small') -> list[Document]:
    """Take a list of Documents, split adaptively, return list of Documents."""
    out_docs = []
    import tiktoken
    enc = tiktoken.encoding_for_model(model)

    for doc in docs:
        text = doc.page_content
        token_count = len(enc.encode(text))

        if token_count < 500:
            out_docs.append(doc)  # keep whole
        elif token_count < 1500:
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                model_name=model, chunk_size=500, chunk_overlap=80
            )
            out_docs.extend(splitter.split_documents([doc]))
        else:
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                model_name=model, chunk_size=800, chunk_overlap=100
            )
            out_docs.extend(splitter.split_documents([doc]))

    return out_docs


def _embedding_dim(embeddings) -> int:
    return len(embeddings.embed_query('dim?'))

def _ensure_collection(client: QdrantClient, name: str, embeddings) -> None:
    if not client.collection_exists(name):
        dim = _embedding_dim(embeddings)
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

# --- Step 4: Batching Helpers ---
def flush_batch(buffer, vs, con):
    """Embed and insert a batch of documents into Qdrant + commit SQLite."""
    if not buffer:
        return

    vs.add_documents(buffer)
    con.commit()
    print(f'  Flushed {len(buffer)} chunks → Qdrant')
    buffer.clear()



# --- Step 5: Main Ingestion ---
def embed_directory_batched(root_dir: str, project_name: str, collection_name: str, batch_size: int = BATCH_SIZE) -> None:
    txt_paths = find_txt_files(root_dir)
    if not txt_paths:
        print(f'No .txt files found under {root_dir}')
        return

    # Initialize DB
    con = ensure_db()

    # Initialize embeddings + vectorstore
    embeddings = OpenAIEmbeddings(model='text-embedding-3-small')

    client = get_qdrant_client(project_name)

    # Ensure collection exists
    _ensure_collection(client, collection_name, embeddings)
    vs = Qdrant(client=client, collection_name=collection_name, embeddings=embeddings)

    staging_buffer = []  # holds chunks before flushing

    print(f'Indexing {len(txt_paths)} files from {root_dir} …')
    for path in tqdm(txt_paths, desc='Indexing files'):
        # Step 1: hash check
        h = file_sha256(path)
        if document_exists(con, h):
            print(f'  SKIP (already indexed): {path.relative_to(root_dir)}')
            continue

        # Step 2: parse and insert doc row
        parsed = parse_file(str(path))

        # Step 3: chunk and attach doc_id
        docs = [Document(page_content=parsed['page_content'], metadata=parsed['metadata'])]
        chunks = adaptive_chunk_documents(docs)
        for ch in chunks:
            ch.metadata['doc_id'] = h

        insert_document(con, path, parsed, h, len(chunks))

        # Step 4: stage chunks
        staging_buffer.extend(chunks)
        print(f'  Staged {len(chunks)} chunks from {path.relative_to(root_dir)}')

        # Step 5: flush if buffer full
        if len(staging_buffer) >= batch_size:
            flush_batch(staging_buffer, vs, con)

    # Final flush
    flush_batch(staging_buffer, vs, con)
    # client.close()   # releases the file lock


# local_qdrant.py
def view_vector_store(client, collection_name, limit=20):
    points, _ = client.scroll(
        collection_name=collection_name,
        limit=limit,
    )
    results = []
    for pt in points:
        meta = pt.payload.get("metadata", {})
        results.append({
            "id": pt.id,
            "doc_id": str(meta.get("doc_id", "")),
            "source": str(meta.get("source", "")),
            "date": str(meta.get("date", "")),   # force everything to string
            "page_content": (pt.payload.get("page_content") or "")[:200] + "..."
        })
    return results


from qdrant_client.models import Filter, FieldCondition, MatchValue

def delete_document_from_store(con, client, collection_name: str, doc_id: str) -> None:
    """Delete a document from SQLite and Qdrant using its doc_id."""
    # 1. Delete from Qdrant
    client.delete(
        collection_name=collection_name,
        wait=True,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.doc_id",  # always nested
                    match=MatchValue(value=str(doc_id))
                )
            ]
        ),
    )

    # 2. Delete from SQLite
    delete_document(con, doc_id)
    print(f"Deleted document {doc_id} from DB and Qdrant.")

