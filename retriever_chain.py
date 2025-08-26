# components/retriever_chain.py
from pathlib import Path
import streamlit as st
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from local_qdrant import get_qdrant_client, ensure_collection

prompt = PromptTemplate(
    template="""You are a helpful historical research assistant.

Use the following historical documents to answer the question as accurately and factually as possible.

{context}

Question: {question}
Answer:""",
    input_variables=["context", "question"]
)

def load_chain(project_name: str, collection_name: str):
    embeddings = OpenAIEmbeddings()

    client = get_qdrant_client(project_name)

    # Ensure collection exists before creating vectorstore
    ensure_collection(client, collection_name, embeddings)

    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings
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
