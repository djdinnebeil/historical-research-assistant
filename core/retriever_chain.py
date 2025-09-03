# components/retriever_chain.py
from pathlib import Path
import streamlit as st
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_cohere import CohereRerank
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from config import using_cohere
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue, Range
from qdrant_client.http import models as qdrant_models



from core.vector_store import get_qdrant_client, ensure_collection

prompt = PromptTemplate(
    template="""You are a helpful historical research assistant.

Use the following historical documents to answer the question as accurately and factually as possible.

{context}

Question: {question}
Answer:""",
    input_variables=["context", "question"]
)

def load_chain(project_name: str, collection_name: str, source_types: list = None, year_range: tuple = None):
    """
    Load the retriever chain with optional source type and year filtering.
    
    Args:
        project_name: Name of the project
        collection_name: Name of the collection
        source_types: List of source types to filter by (e.g., ['book', 'journal'])
        year_range: Tuple of (start_year, end_year) for filtering
    """
    embeddings = OpenAIEmbeddings()

    client = get_qdrant_client(project_name)

    # Ensure collection exists before creating vectorstore
    ensure_collection(client, collection_name, embeddings)

    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings
    )
    
    # Build filter conditions
    filter_conditions = []
    
    # Add source type filter if specified
    if source_types and len(source_types) > 0:
        filter_conditions.append(
            FieldCondition(
                key="metadata.source_type",
                match=MatchAny(any=source_types)
            )
        )
    
    if year_range:
        start_year, end_year = year_range
        print(start_year, end_year)
        filter_conditions.append(
            FieldCondition(
                key="metadata.year",
                range={"gte":start_year, "lte":end_year}
            ))

    # Create retriever with or without filters
    if filter_conditions:
        qdrant_filter = Filter(must=filter_conditions)
        naive_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 15, "filter": qdrant_filter}
        )
    else:
        naive_retriever = vectorstore.as_retriever(search_kwargs={"k": 15})

    # Apply contextual compression if using_cohere is True
    if using_cohere:
        compressor = CohereRerank(model="rerank-v3.5")
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=naive_retriever, top_k=12
        )
        final_retriever = compression_retriever
    else:
        final_retriever = naive_retriever

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=final_retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    if using_cohere:
        return qa_chain, naive_retriever, compression_retriever
    else:
        return qa_chain, naive_retriever