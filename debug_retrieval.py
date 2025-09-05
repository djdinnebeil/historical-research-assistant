#!/usr/bin/env python3
"""
Debug Retrieval Tool

This script helps debug retrieval issues by testing different retrieval strategies
and showing what documents are being returned for a given query.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.retriever_chain import load_chain
from core.vector_store import get_qdrant_client
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Filter, FieldCondition, MatchAny
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_retrieval(project_name: str, collection_name: str, query: str, source_types: list = None, year_range: tuple = None):
    """Debug retrieval for a specific query"""
    
    print(f"🔍 Debugging retrieval for query: '{query}'")
    print(f"Project: {project_name}, Collection: {collection_name}")
    print("=" * 80)
    
    try:
        # Load the chain
        result = load_chain(project_name, collection_name, source_types, year_range)
        if len(result) == 3:
            qa_chain, naive_retriever, compression_retriever = result
        else:
            qa_chain, naive_retriever = result
        
        # Test retrieval
        if hasattr(qa_chain, 'test_retrieval'):
            naive_docs, final_docs = qa_chain.test_retrieval(query)
            
            print(f"\n📊 RETRIEVAL RESULTS:")
            print(f"Naive retriever returned: {len(naive_docs)} documents")
            print(f"Final retriever returned: {len(final_docs)} documents")
            
            print(f"\n📄 NAIVE RETRIEVER RESULTS:")
            for i, doc in enumerate(naive_docs[:10]):  # Show first 10
                print(f"\n--- Document {i+1} ---")
                print(f"Content: {doc.page_content[:200]}...")
                if hasattr(doc, 'metadata') and doc.metadata:
                    print(f"Metadata: {doc.metadata}")
            
            print(f"\n📄 FINAL RETRIEVER RESULTS:")
            for i, doc in enumerate(final_docs[:10]):  # Show first 10
                print(f"\n--- Document {i+1} ---")
                print(f"Content: {doc.page_content[:200]}...")
                if hasattr(doc, 'metadata') and doc.metadata:
                    print(f"Metadata: {doc.metadata}")
        
        # Test different retrieval strategies
        if hasattr(qa_chain, 'test_retrieval_strategies'):
            print(f"\n🔍 TESTING DIFFERENT RETRIEVAL STRATEGIES:")
            strategies = qa_chain.test_retrieval_strategies(query)
            
            for strategy in strategies:
                print(f"\n--- {strategy['name'].upper()} ---")
                print(f"Retrieved {strategy['count']} documents")
                for i, doc in enumerate(strategy['docs'][:5]):  # Show first 5
                    print(f"  {i+1}. {doc.page_content[:100]}...")
                    if 'scores' in strategy:
                        print(f"     Score: {strategy['scores'][i]:.4f}")
        
        # Test direct similarity search
        print(f"\n🔍 DIRECT SIMILARITY SEARCH TEST:")
        client = get_qdrant_client(project_name)
        embeddings = OpenAIEmbeddings()
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings
        )
        
        # Test with different k values
        for k in [5, 15, 30, 50]:
            print(f"\n--- Testing with k={k} ---")
            results = vectorstore.similarity_search(query, k=k)
            print(f"Retrieved {len(results)} documents")
            for i, doc in enumerate(results[:3]):  # Show first 3
                print(f"  {i+1}. {doc.page_content[:100]}...")
        
        # Test with similarity search with scores
        print(f"\n📊 SIMILARITY SEARCH WITH SCORES:")
        results_with_scores = vectorstore.similarity_search_with_score(query, k=10)
        for i, (doc, score) in enumerate(results_with_scores):
            print(f"{i+1}. Score: {score:.4f} - {doc.page_content[:100]}...")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) < 4:
        print("Usage: python debug_retrieval.py <project_name> <collection_name> <query> [source_types] [year_range]")
        print("Example: python debug_retrieval.py amatol_project amatol_project_docs 'What is amatol?'")
        sys.exit(1)
    
    project_name = sys.argv[1]
    collection_name = sys.argv[2]
    query = sys.argv[3]
    
    source_types = None
    year_range = None
    
    if len(sys.argv) > 4:
        source_types = sys.argv[4].split(',') if sys.argv[4] else None
    
    if len(sys.argv) > 5:
        try:
            start_year, end_year = map(int, sys.argv[5].split(','))
            year_range = (start_year, end_year)
        except ValueError:
            print("Invalid year range format. Use: start_year,end_year")
            sys.exit(1)
    
    debug_retrieval(project_name, collection_name, query, source_types, year_range)

if __name__ == "__main__":
    main()
