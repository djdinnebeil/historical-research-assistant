# rag_ui_streamlit.py
import streamlit as st
from langgraph_agent import build_agent_graph
from langchain_core.messages import HumanMessage
import config 
from db import *

# Testing
testing = False

from retriever_chain import load_chain

@st.cache_resource
def initialize_chains():
    """Cache the expensive chain initialization"""
    return load_chain()

@st.cache_resource  
def initialize_agent():
    """Cache the expensive agent graph compilation"""
    return build_agent_graph()

qa_chain, naive_retriever = initialize_chains()
compiled_graph = initialize_agent()

# --- Streamlit UI ---
mode = st.radio(
    "Select mode:",
    options=["Standard QA", "Agentic Workflow"],
    help="Standard QA uses your compression retriever; Agentic Workflow lets the LLM decide whether to use tools like Tavily search."
)

st.title("Historical Research Assistant")
question = st.text_input("Ask a question about your documents:")

if question:
    try:
        with st.spinner("Searching historical documents..."):
            
            if mode == "Standard QA":
                # Optional diagnostics
                if testing:
                    retrieved_docs = naive_retriever.get_relevant_documents(question)

                    for i, doc in enumerate(retrieved_docs):
                        source = doc.metadata.get("source", "unknown")
                        st.markdown(f"**Naive {i+1}** — `{source}`\n\n{doc.page_content[:300]}...")

                    st.write("--------------------------------")

                # Run QA
                result = qa_chain(question)

                st.success("Answer ready!")
                st.subheader("📜 Answer")
                st.write(result["result"])

                st.subheader("📁 Sources consulted")
                sources = set(doc.metadata.get("citation", "unknown") for doc in result["source_documents"])
                for source in sorted(sources):
                    st.markdown(f"- `{source}`")

            else:  # Agentic workflow
                response = compiled_graph.invoke({
                    "messages": [HumanMessage(content=question)],
                    "context": []
                })

                final_answer = response["messages"][-1].content
                st.success("Answer from agent ready!")
                st.subheader("📜 Answer")
                st.write(final_answer)

                # Display comprehensive tool usage information
                st.subheader("🔧 Tool Usage Details")
                
                # Collect all tool calls from the conversation
                tool_calls = []
                tool_results = []
                
                for msg in response["messages"]:
                    # Check for tool calls in AI messages
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_calls.append({
                                'name': tool_call['name'],
                                'args': tool_call.get('args', {}),
                                'id': tool_call.get('id', 'unknown')
                            })
                    
                    # Check for tool results
                    if hasattr(msg, 'name') and msg.name in ['tavily_search_tool', 'historical_rag_tool']:
                        tool_results.append({
                            'tool': msg.name,
                            'content': msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                        })
                
                if tool_calls:
                    st.write("**Tools Called:**")
                    for i, tool_call in enumerate(tool_calls, 1):
                        st.write(f"{i}. `{tool_call['name']}`")
                        if tool_call['args']:
                            with st.expander(f"View arguments for {tool_call['name']}"):
                                st.json(tool_call['args'])
                    
                    st.info(f"Total tools used: {len(tool_calls)}")
                    
                    # Show which tools were used
                    tools_used = set(tc['name'] for tc in tool_calls)
                    if 'historical_rag_tool' in tools_used and 'tavily_search_tool' in tools_used:
                        st.success("✅ Both historical documents and web search were used!")
                    elif 'historical_rag_tool' in tools_used:
                        st.info("📚 Only historical documents were searched")
                    elif 'tavily_search_tool' in tools_used:
                        st.info("🌐 Only web search was used")
                    
                    # Show tool results preview
                    if tool_results:
                        with st.expander("Tool Results Preview"):
                            for result in tool_results:
                                st.write(f"**{result['tool']}:**")
                                st.write(result['content'])
                                st.write("---")
                else:
                    st.warning("No tools were used in this response")
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try rephrasing your question or check your API keys.")

import pandas as pd
from local_qdrant import view_vector_store
from retriever_chain import get_qdrant_client
import config

st.sidebar.subheader("🔍 Inspect Vector Store")
if st.sidebar.button("View Qdrant Contents"):
    try:
        client = get_qdrant_client(config.PROJECT_NAME)  # reuse cached client
        data = view_vector_store(client, config.COLLECTION_NAME, limit=20)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.info("No vectors found in the collection.")
    except Exception as e:
        st.error(f"Error reading Qdrant: {e}")

import pandas as pd
from db import ensure_db, list_all_documents
from local_qdrant import delete_document_from_store
from retriever_chain import get_qdrant_client
import config

st.sidebar.subheader("📄 Inspect & Manage SQLite Database")

# Session flag
if "show_docs" not in st.session_state:
    st.session_state.show_docs = False

if st.sidebar.button("View All Documents"):
    st.session_state.show_docs = True   # turn on persistent view

if st.session_state.show_docs:
    try:
        con = ensure_db()
        rows = list_all_documents(con)
        if rows:
            col_names = [desc[1] for desc in con.execute("PRAGMA table_info(documents)")]  
            df = pd.DataFrame(rows, columns=col_names)

            st.write("### Documents in Database")
            for _, row in df.iterrows():
                st.markdown(f"""
                **Citation**: {row['citation']}  
                **Source Type**: {row['source_type']}  
                **Date**: {row['date']}  
                **Doc ID**: `{row['content_hash']}`
                """)
                if st.button(f"🗑️ Delete {row['content_hash']}", key=row['content_hash']):
                    try:
                        client = get_qdrant_client(config.PROJECT_NAME)
                        delete_document_from_store(con, client, config.COLLECTION_NAME, row['content_hash'])
                        st.success(f"Deleted document {row['content_hash']}")
                    except Exception as e:
                        st.error(f"Error deleting document {row['content_hash']}: {e}")
                st.divider()
        else:
            st.info("No documents found in the database.")
    except Exception as e:
        st.error(f"Error reading database: {e}")
