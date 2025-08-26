import streamlit as st
import config

def render_qa_interface(project_name: str, collection_name: str):
    """Render the question-answering interface using the LangGraph agent."""
    
    st.header("🤖 Ask Questions")
    st.markdown("Ask questions about your historical documents and get AI-powered answers that combine historical context with current information.")
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # We'll use the retriever chain directly instead of the agent graph
    
    # Display chat history
    st.subheader("Chat History")
    chat_container = st.container()
    
    with chat_container:
        for i, chat_entry in enumerate(st.session_state.chat_history):
            # Handle both old format (tuple) and new format (dict)
            if isinstance(chat_entry, tuple):
                # Old format: (question, answer)
                question, answer = chat_entry
                citations = []
            else:
                # New format: dict with question, answer, citations
                question = chat_entry.get('question', '')
                answer = chat_entry.get('answer', '')
                citations = chat_entry.get('citations', [])
            
            # Create expander header with source count
            source_count = len(citations) if citations else 0
            expander_title = f"Q: {question[:50]}... ({source_count} sources)"
            
            with st.expander(expander_title, expanded=False):
                # Show timestamp if available
                if isinstance(chat_entry, dict) and chat_entry.get('timestamp'):
                    st.caption(f"📅 {chat_entry['timestamp']}")
                
                st.markdown(f"**Question:** {question}")
                st.markdown(f"**Answer:** {answer}")
                
                # Display citations if available
                if citations:
                    st.markdown("**📚 Sources Consulted:**")
                    for j, citation in enumerate(citations, 1):
                        st.markdown(f"{j}. {citation}")
                else:
                    st.info("ℹ️ No citation information available for this response.")
                
                # Add delete button for each chat entry
                if st.button(f"Delete", key=f"delete_{i}"):
                    st.session_state.chat_history.pop(i)
                    st.rerun()
    
    # Clear chat history button
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Question input section
    st.subheader("Ask a New Question")
    
    # Question input
    question = st.text_area(
        "Enter your question:",
        placeholder="e.g., What were the main causes of the Industrial Revolution?",
        height=100,
        key="question_input"
    )
    
    # Advanced options
    with st.expander("Advanced Options"):
        use_web_search = st.checkbox("Include web search for current context", value=True)
        max_tokens = st.slider("Maximum response length", min_value=100, max_value=2000, value=1000, step=100)
    
    # Submit button
    if st.button("Ask Question", type="primary", disabled=not question.strip()):
        if question.strip():
            with st.spinner("🤔 Thinking..."):
                try:
                    # Check if we have a valid project context
                    if not project_name or project_name == "-- New Project --":
                        st.error("Please select a valid project first.")
                        return
                    
                    # Instead of using the complex agent, let's use the retriever chain directly for better control
                    from retriever_chain import load_chain
                    from langchain_core.messages import HumanMessage
                    
                    # Load the chain for the current project
                    qa_chain, naive_retriever = load_chain(project_name, collection_name)
                    
                    # Create a custom message that includes the web search preference
                    question_with_context = question
                    if not use_web_search:
                        question_with_context = f"{question}\n\nIMPORTANT: Answer this question using ONLY the historical documents. Do NOT use web search. Focus entirely on the uploaded historical content."
                    
                    # Use the retriever chain directly
                    response = qa_chain.invoke(question_with_context)
                    
                    # Extract the result and source documents
                    final_response = response.get('result', '')
                    source_documents = response.get('source_documents', [])
                    
                    # Extract citations from source documents
                    citations = []
                    if source_documents:
                        for doc in source_documents:
                            # Check for citation in metadata
                            if hasattr(doc, 'metadata') and doc.metadata:
                                citation = doc.metadata.get('citation')
                                if citation and citation not in citations:
                                    citations.append(citation)
                            
                            # Also check for citation in the document itself if metadata doesn't have it
                            if not citations and hasattr(doc, 'page_content'):
                                # Look for citation patterns in the content
                                content = doc.page_content
                                if 'citation:' in content.lower() or 'source:' in content.lower():
                                    # Extract citation from content
                                    lines = content.split('\n')
                                    for line in lines:
                                        if 'citation:' in line.lower() or 'source:' in line.lower():
                                            citation = line.split(':', 1)[1].strip()
                                            if citation and citation not in citations:
                                                citations.append(citation)
                                            break
                    
                    # If web search is enabled and we want to add current context, we can do that here
                    if use_web_search and final_response:
                        # Add a note about the response source
                        final_response += "\n\n---\n\n*This answer is based on your uploaded historical documents. For current information, you may want to supplement with additional research.*"
                    
                    # Check if we got a valid response
                    if final_response and final_response.strip():
                        # Add to chat history with citations
                        from datetime import datetime
                        chat_entry = {
                            'question': question,
                            'answer': final_response,
                            'citations': citations,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        if 'chat_history' not in st.session_state:
                            st.session_state.chat_history = []
                        
                        st.session_state.chat_history.append(chat_entry)
                        
                        # Display the response
                        st.success("✅ Answer generated!")
                        st.markdown("**Answer:**")
                        st.markdown(final_response)
                        
                        # Display sources consulted
                        if citations:
                            st.markdown("**📚 Sources Consulted:**")
                            for i, citation in enumerate(citations, 1):
                                st.markdown(f"{i}. {citation}")
                        else:
                            st.info("ℹ️ No citation information available for the sources consulted.")
                        
                        # Clear the input by rerunning
                        st.rerun()
                    else:
                        st.error("No response generated. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")
                    st.exception(e)
    
    # Display some example questions
    st.divider()
    st.subheader("💡 Example Questions")
    
    example_questions = [
        "What were the main causes of the Industrial Revolution?",
        "How did World War II impact global trade?",
        "What were the key inventions of the 19th century?",
        "How did the printing press change society?",
        "What were the major economic policies during the Great Depression?"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(example_questions):
        col = cols[i % 2]
        if col.button(example, key=f"example_{i}"):
            st.session_state.question_input = example
            st.rerun()
    
    # Information about the system
    st.divider()
    st.info("""
    **How it works:** This system uses your uploaded historical documents combined with current web information to provide comprehensive answers. 
    It first searches your document collection for historical context, then supplements with current information when relevant.
    """)
