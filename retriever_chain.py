# components/retriever_chain.py
from pathlib import Path
import streamlit as st
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from config import COLLECTION_NAME, PROJECT_NAME

prompt = PromptTemplate(
    template="""You are a helpful historical research assistant.

Use the following historical documents to answer the question as accurately and factually as possible.

{context}

Question: {question}
Answer:""",
    input_variables=["context", "question"]
)

# ✅ Cache the Qdrant client so reloads don’t re-lock the DB
@st.cache_resource
def get_qdrant_client(project_name: str):
    project_dir = Path("projects") / project_name
    qdrant_path = project_dir / "qdrant"
    qdrant_path.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(qdrant_path))

def load_chain():
    embeddings = OpenAIEmbeddings()

    client = get_qdrant_client(PROJECT_NAME)

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )
    naive_retriever = vectorstore.as_retriever(search_kwargs={"k": 15})

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=naive_retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    return qa_chain, naive_retriever
