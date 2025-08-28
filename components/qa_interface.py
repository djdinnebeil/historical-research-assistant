import streamlit as st
import config

def render_qa_interface(project_name: str, collection_name: str):
    """Render the question-answering interface using the LangGraph agent."""
    
    st.header("🤖 Ask Questions")
    st.markdown("Ask questions about your historical documents and get AI-powered answers that combine historical context with current information.")
    
    # Mode selection toggle
    st.subheader("🔧 Select Mode")
    mode = st.radio(
        "Choose your search mode:",
        options=["Standard", "Advanced"],
        help="Standard: Uses only your uploaded historical documents. Advanced: Combines historical documents with web search for current context.",
        index=0  # Default to Standard
    )
    
    st.divider()
    
    # Filter section
    st.subheader("🔍 Filter Sources")
    
    # Source type filter
    source_types = st.multiselect(
        "Select source types to include:",
        options=["book", "journal", "newspaper", "report", "web_article", "misc", "unsorted"],
        default=["book", "journal", "newspaper", "report", "web_article", "misc", "unsorted"],
        help="Select one or more source types to filter your search. Leave all selected to search all sources.",
        key="source_type_filter"
    )
    
    # Year range filter
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input(
            "Start Year:",
            min_value=1000,
            max_value=2024,
            value=1000,
            help="Earliest year to include in search (leave at 1000 for no lower limit)"
        )
    
    with col2:
        end_year = st.number_input(
            "End Year:",
            min_value=1000,
            max_value=2024,
            value=2024,
            help="Latest year to include in search (leave at 2024 for no upper limit)"
        )
    
    # Filter summary
    if source_types and len(source_types) < 7:
        st.info(f"🔍 **Active Filters:** Source types: {', '.join(source_types)} | Year range: {start_year}-{end_year}")
    elif start_year > 1000 or end_year < 2024:
        st.info(f"🔍 **Active Filters:** Year range: {start_year}-{end_year}")
    else:
        st.info("🔍 **No active filters** - searching all sources and years")
    
    st.divider()
    
    # Question input section
    st.subheader("Ask a New Question")
    
    # Question input with better real-time state management using text_input
    question = st.text_input(
        "Enter your question:",
        placeholder="e.g., What were the main causes of the Industrial Revolution?",
        key="question_input"
    )
    
    # Advanced options (only show for advanced mode)
    if mode == "Advanced":
        with st.expander("Advanced Options"):
            max_tokens = st.slider("Maximum response length", min_value=100, max_value=2000, value=1000, step=100)
            st.info("Advanced mode will use both your historical documents and web search for comprehensive answers.")
    
    # Submit button - always enabled for better UX
    if st.button("Ask Question", type="primary"):
        if question.strip():
            with st.spinner("Thinking..."):
                try:
                    # Check if we have a valid project context
                    if not project_name or project_name == "-- New Project --":
                        st.error("Please select a valid project first.")
                        return
                    
                    # Initialize variables for both modes
                    citations = []
                    web_sources = []
                    tools_used = []
                    file_paths = []

                    if mode == "Standard":
                        # Standard mode: Use only the retriever chain (vector store)
                        from retriever_chain import load_chain
                        
                        # Load the chain for the current project with filters
                        qa_chain, naive_retriever = load_chain(
                            project_name, 
                            collection_name, 
                            source_types=source_types if source_types else None,
                            year_range=(start_year, end_year) if start_year > 1000 or end_year < 2024 else None
                        )
                        
                        # Use the retriever chain directly (vector store only)
                        response = qa_chain.invoke(question)
                        
                        # Extract the result and source documents
                        final_response = response.get('result', '')
                        source_documents = response.get('source_documents', [])
                        
                        # Extract citations from source documents
                        citations = []
                        if source_documents:
                            for i, doc in enumerate(source_documents):
                                # Check for citation in metadata
                                if hasattr(doc, 'metadata') and doc.metadata:
                                    citation = doc.metadata.get('citation')
                                    file_path = doc.metadata.get('file_path')
                                    if citation and citation not in citations:
                                        citations.append(citation)
                                        file_paths.append(file_path)
                                
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
                        tools_used = ["Vector Store (Historical Documents)"]
                        
                    else:  # Advanced mode
                        # Advanced mode: Use the agent graph with web search
                        from langgraph_agent import build_agent_graph
                        from langchain_core.messages import HumanMessage
                        
                        # Build the agent graph (already compiled)
                        agent_graph = build_agent_graph()
                        
                        # Create a system message with project context and filters
                        from langchain_core.messages import SystemMessage
                        filter_info = ""
                        if source_types and len(source_types) < 7:
                            filter_info += f"\nSource type filter: {', '.join(source_types)}"
                        if start_year > 1000 or end_year < 2024:
                            filter_info += f"\nYear range filter: {start_year}-{end_year}"
                        
                        # Prepare filter parameters for the tool call
                        filter_params = ""
                        if source_types and len(source_types) < 7:
                            filter_params += f', source_types={source_types}'
                        if start_year > 1000 or end_year < 2024:
                            filter_params += f', year_range=({start_year}, {end_year})'
                        
                        project_context = f"""Current project: {project_name}
Current collection: {collection_name}{filter_info}

WORKFLOW REQUIREMENTS:
1. You MUST call historical_rag_tool FIRST with these exact parameters:
   historical_rag_tool(question="{question}", project_name="{project_name}", collection_name="{collection_name}"{filter_params})

2. You MUST call tavily_search_tool SECOND with a relevant query about the topic.

3. You are NOT allowed to provide any answer until BOTH tools have been called.

4. After calling both tools, combine their results in your final answer.

This is a mandatory requirement - you cannot skip either tool."""
                        
                        response = agent_graph.invoke({
                            "messages": [
                                SystemMessage(content=project_context),
                                HumanMessage(content=question)
                            ],
                            "context": []
                        })
                        
                        # Extract the final answer
                        final_response = response["messages"][-1].content
                        
                        # Extract citations and tool usage information from tool responses
                        for msg in response["messages"]:
                            # Check for tool calls in AI messages
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call['name']
                                    if tool_name not in tools_used:
                                        tools_used.append(tool_name)
                            
                            # Check for tool results and extract citations from historical_rag_tool
                            if hasattr(msg, 'name') and msg.name == 'historical_rag_tool':
                                if msg.name not in tools_used:
                                    tools_used.append(msg.name)
                                
                                # Extract citations from the tool response content
                                if hasattr(msg, 'content') and msg.content:
                                    content = msg.content
                                    
                                    # Look for the SOURCE DOCUMENTS section
                                    if '--- SOURCE DOCUMENTS ---' in content:
                                        source_section = content.split('--- SOURCE DOCUMENTS ---')[1]
                                        
                                        # Extract citations from each source
                                        lines = source_section.split('\n')
                                        for i, line in enumerate(lines):
                                            # Only match lines that start with "Source " followed by a number
                                            if line.strip().startswith('Source ') and ':' in line:
                                                # Check if it's actually a source line (Source 1:, Source 2:, etc.)
                                                parts = line.split(':', 1)
                                                if len(parts) == 2:
                                                    source_part = parts[0].strip()
                                                    citation = parts[1].strip()
                                                    
                                                    # Verify it's a proper source line (Source 1, Source 2, etc.)
                                                    if source_part.startswith('Source ') and source_part[7:].isdigit():
                                                        if citation and citation != 'Unknown source' and citation not in citations:
                                                            citations.append(citation)
                            
                            # Check for tavily search tool usage and extract web sources
                            if hasattr(msg, 'name') and msg.name == 'tavily_search_tool':
                                if msg.name not in tools_used:
                                    tools_used.append(msg.name)
                                
                                # Extract web search results from the tool response content
                                if hasattr(msg, 'content') and msg.content:
                                    content = msg.content
                                    
                                    # Look for web search results
                                    if 'Web search results:' in content:
                                        # Extract the web search results section
                                        web_section = content.split('Web search results:')[1]
                                        
                                        # Parse web search results (format: "1. Title — URL")
                                        lines = web_section.split('\n')
                                        for line in lines:
                                            line = line.strip()
                                            if line and line[0].isdigit() and ' — ' in line:
                                                # Extract title and URL
                                                parts = line.split(' — ', 1)
                                                if len(parts) == 2:
                                                    title = parts[0].split('. ', 1)[1] if '. ' in parts[0] else parts[0]
                                                    url = parts[1]
                                                    web_source = f"{title} — {url}"
                                                    if web_source not in web_sources:
                                                        web_sources.append(web_source)
                        
                        # If no tools were used, add default
                        if not tools_used:
                            tools_used = ["Vector Store (Historical Documents)"]
                        

                    
                    # Check if we got a valid response
                    if final_response and final_response.strip():
                        # Add to chat history with citations, tools used, and mode
                        from datetime import datetime
                        
                        # For advanced mode, combine citations and web sources
                        all_sources = citations.copy()
                        if mode == "Advanced" and web_sources:
                            all_sources.extend(web_sources)
                        
                        chat_entry = {
                            'question': question,
                            'answer': final_response,
                            'citations': all_sources,  # Include both historical and web sources
                            'web_sources': web_sources,  # Keep web sources separate for display
                            'tools_used': tools_used,
                            'mode_used': mode,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Save to database
                        from db import insert_chat_entry
                        # Get database connection from session state
                        if "db_client" in st.session_state:
                            con, _ = st.session_state.db_client
                            insert_chat_entry(con, question, final_response, mode, citations, web_sources, tools_used, project_name)
                            st.success("✅ Answer generated and saved to chat history!")
                        else:
                            st.warning("Database connection not available. Chat history not saved.")
                            st.success("✅ Answer generated!")
                        
                        # Display the response
                        st.markdown("**Answer:**")
                        st.markdown(final_response)
                        
                        # Display mode used
                        st.markdown(f"**Mode:** {mode}")
                        
                        # Display active filters used
                        if source_types and len(source_types) < 7 or start_year > 1000 or end_year < 2024:
                            st.markdown("**🔍 Filters Applied:**")
                            if source_types and len(source_types) < 7:
                                st.markdown(f"- **Source Types:** {', '.join(source_types)}")
                            if start_year > 1000 or end_year < 2024:
                                st.markdown(f"- **Year Range:** {start_year}-{end_year}")
                        
                        # Display sources consulted
                        if citations or web_sources:
                            st.markdown("**📚 Sources Consulted:**")
                            
                            # For advanced mode, separate historical citations from web sources
                            if mode == "Advanced" and web_sources:
                                # Filter out web sources from citations to get historical ones
                                historical_citations = [c for c in citations if c not in web_sources]
                                
                                # Display historical document sources
                                if historical_citations:
                                    st.markdown("**Historical Documents:**")
                                    for i, citation in enumerate(historical_citations, 1):
                                        st.markdown(f"{i}. {citation}")
                                
                                # Display web sources
                                if web_sources:
                                    if historical_citations:  # Add spacing if we had historical sources
                                        st.markdown("")
                                    st.markdown("**Web Sources:**")
                                    for i, web_source in enumerate(web_sources, len(historical_citations) + 1):
                                        st.markdown(f"{i}. {web_source}")
                            else:
                                # Standard mode or no web sources - display all citations as historical
                                if citations:
                                    st.markdown("**Historical Documents:**")
                                    for i, citation in enumerate(citations, 1):
                                        st.markdown(f"{i}. {citation}")
                                        
                                        # Add expander to show file contents
                                        if i <= len(file_paths) and file_paths[i-1]:
                                            try:
                                                with open(file_paths[i-1], 'r', encoding='utf-8') as f:
                                                    file_content = f.read()
                                                
                                                with st.expander(f"📄 View file contents: {file_paths[i-1].split('/')[-1]}"):
                                                    # Custom CSS to improve text readability and cursor
                                                    st.markdown(file_content)
                                                  
                                            except Exception as e:
                                                with st.expander(f"📄 View file contents: {file_paths[i-1].split('/')[-1]}"):
                                                    st.error(f"Error reading file: {str(e)}")
                                        else:
                                            with st.expander("📄 View file contents"):
                                                st.info("File path not available for this citation.")

                        else:
                            st.info("ℹ️ No citation information available for the sources consulted.")
                        
                        # Display tools used for advanced mode
                        if mode == "Advanced" and tools_used:
                            st.markdown("**🔧 Tools Used:**")
                            for tool in tools_used:
                                st.markdown(f"- {tool}")
                        
                        # Show a note about where to find the full conversation
                        st.info("💡 **Full conversation saved to chat history!** You can view it in the 'Chat History' section of the sidebar.")
                        
                        # Add a button to ask another question
                        if st.button("Ask Another Question", type="secondary"):
                            st.rerun()
                    else:
                        st.error("No response generated. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")
                    st.exception(e)
    

    # Information about the system
    st.divider()
    st.info(f"""
    **How it works:** 
    
    **Standard Mode:** Uses only your uploaded historical documents through the vector store for focused, document-based answers.
    
    **Advanced Mode:** Combines your historical documents with web search to provide comprehensive answers that include both historical context and current information.
    
    **Filtering:** You can filter by source type (book, journal, newspaper, etc.) and year range to focus your search on specific types of documents or time periods.
    
    Current mode: **{mode}**
    
    💡 **Tip:** Your chat history is automatically saved and can be viewed in the "Chat History" section of the sidebar.
    """)
