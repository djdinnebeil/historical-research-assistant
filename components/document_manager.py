import streamlit as st
from db import list_all_documents, delete_document
from local_qdrant import get_qdrant_client
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
import json

COLUMNS = [
    "id", "path", "citation", "source_type", "source_id",
    "date", "num_chunks", "content_hash", "status", "added_at"
]

def render_document_manager(proj_dir, con, collection_name):
    st.subheader("📚 Document Manager")
    
    # Get all documents from database
    try:
        all_documents = list_all_documents(con)
        
        if not all_documents:
            st.info("No documents found in the database.")
            return
        
        st.write(f"**Total Documents:** {len(all_documents)}")
        
        # Count by status
        status_counts = {}
        for doc in all_documents:
            status = doc[8]  # status is at index 8
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Display status summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pending", status_counts.get("pending", 0))
        with col2:
            st.metric("Embedded", status_counts.get("embedded", 0))
        with col3:
            st.metric("Total", len(all_documents))
        
        # Filter options
        st.subheader("🔍 Filter Documents")
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "pending", "embedded"],
                index=0
            )
        
        with col2:
            search_term = st.text_input("Search by path or citation:", placeholder="Enter search term...")
        
        # Apply filters
        filtered_docs = all_documents
        if status_filter != "All":
            filtered_docs = [doc for doc in filtered_docs if doc[8] == status_filter]
        
        if search_term:
            filtered_docs = [doc for doc in filtered_docs 
                           if search_term.lower() in str(doc[1]).lower() or 
                              search_term.lower() in str(doc[2]).lower()]
        
        st.write(f"**Filtered Results:** {len(filtered_docs)} documents")
        
        # Display documents
        st.subheader("📋 Document List")
        
        for i, doc in enumerate(filtered_docs):
            record = dict(zip(COLUMNS, doc))
            
            # Create a unique key for each document
            doc_key = f"doc_{record['id']}_{record['content_hash'][:8]}"
            
            # Document header with status indicator
            status_color = "🟡" if record['status'] == 'pending' else "🟢"
            header_text = f"{status_color} {Path(record['path']).name} ({record['status']})"
            
            with st.expander(header_text, expanded=False):
                # Document details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Path:**", record['path'])
                    
                    # Show the actual file path being used
                    if Path(record['path']).is_absolute():
                        actual_path = Path(record['path'])
                    else:
                        # Try multiple possible path combinations
                        possible_paths = [
                            proj_dir / record['path'],  # Original path
                            proj_dir / "documents" / record['path'],  # Add documents/ prefix
                            proj_dir / "documents" / Path(record['path']).name  # Just filename
                        ]
                        
                        # Find the first path that exists
                        actual_path = None
                        for path in possible_paths:
                            if path.exists():
                                actual_path = path
                                break
                        
                        # If no path found, use the first one for display
                        if actual_path is None:
                            actual_path = possible_paths[0]
                    
                    st.write("**Full Path:**", str(actual_path))
                    st.write("**File Exists:**", "✅ Yes" if actual_path.exists() else "❌ No")
                    
                    # Show all attempted paths for debugging
                    if not actual_path.exists() and not Path(record['path']).is_absolute():
                        st.write("**Attempted Paths:**")
                        for i, path in enumerate(possible_paths):
                            exists = "✅" if path.exists() else "❌"
                            st.write(f"  {i+1}. {exists} {path}")
                    
                    if record['citation']:
                        st.write("**Citation:**", record['citation'])
                    if record['source_type']:
                        st.write("**Source Type:**", record['source_type'])
                    if record['source_id']:
                        st.write("**Source ID:**", record['source_id'])
                    if record['date']:
                        st.write("**Date:**", record['date'])
                    st.write("**Added:**", record['added_at'])
                    st.write("**Chunks:**", record['num_chunks'] or "N/A")
                    st.write("**Content Hash:**", record['content_hash'][:16] + "...")
                
                with col2:
                    # Action buttons
                    if st.button("👁️ View Details", key=f"view_{doc_key}"):
                        st.session_state[f"show_details_{doc_key}"] = True
                    
                    if st.button("🗑️ Delete", key=f"delete_{doc_key}", type="secondary"):
                        st.session_state[f"confirm_delete_{doc_key}"] = True
                
                # Show detailed view if requested
                if st.session_state.get(f"show_details_{doc_key}", False):
                    st.subheader("📄 Full Document Details")
                    st.json(record)
                    
                    # Show file content if available
                    try:
                        # Handle both absolute and relative paths
                        if Path(record['path']).is_absolute():
                            file_path = Path(record['path'])
                        else:
                            # Try multiple possible path combinations
                            possible_paths = [
                                proj_dir / record['path'],  # Original path
                                proj_dir / "documents" / record['path'],  # Add documents/ prefix
                                proj_dir / "documents" / Path(record['path']).name  # Just filename
                            ]
                            
                            # Find the first path that exists
                            file_path = None
                            for path in possible_paths:
                                if path.exists():
                                    file_path = path
                                    break
                            
                            # If no path found, use the first one for error reporting
                            if file_path is None:
                                file_path = possible_paths[0]
                        
                        if file_path.exists():
                            st.subheader("📖 File Content Preview")
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                st.text_area("Content:", content, height=200, disabled=True)
                        else:
                            st.warning(f"File not found at: {file_path}")
                            st.info(f"Database path: {record['path']}")
                            st.info(f"Project directory: {proj_dir}")
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                        st.info(f"Attempted path: {file_path}")
                
                # Delete confirmation
                if st.session_state.get(f"confirm_delete_{doc_key}", False):
                    st.warning("⚠️ Are you sure you want to delete this document?")
                    st.write("**This action will:**")
                    st.write("- Remove the document from the database")
                    
                    if record['status'] == 'embedded':
                        st.write("- Remove all associated vectors from the vector store")
                        st.write("- This action cannot be undone!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("✅ Confirm Delete", key=f"confirm_{doc_key}", type="primary"):
                            try:
                                # Delete from database
                                delete_document(con, record['content_hash'])
                                
                                # If embedded, also remove from vector store
                                if record['status'] == 'embedded':
                                    try:
                                        project_name = proj_dir.name
                                        client = get_qdrant_client(project_name)
                                        
                                                                                # Get Qdrant client and remove vectors
                                        if client.collection_exists(collection_name):
                                            deleted_count = 0
                                            
                                            # Strategy 1: Try to find vectors by content_hash in metadata
                                            try:
                                                points = client.scroll(
                                                    collection_name=collection_name,
                                                    scroll_filter={
                                                        "must": [
                                                            {
                                                                "key": "content_hash",
                                                                "match": {"value": record['content_hash']}
                                                            }
                                                        ]
                                                    },
                                                    limit=1000,
                                                    with_payload=False,
                                                    with_vectors=False
                                                )
                                                
                                                if points[0]:  # points are in first element
                                                    point_ids = [point.id for point in points[0]]
                                                    if point_ids:
                                                        client.delete(
                                                            collection_name=collection_name,
                                                            points_selector=point_ids
                                                        )
                                                        deleted_count += len(point_ids)
                                                        st.success(f"✅ Deleted {len(point_ids)} vectors by content_hash")
                                            except Exception as e:
                                                st.info(f"Strategy 1 (content_hash) failed: {str(e)}")
                                            
                                            # Strategy 2: If no vectors found by content_hash, try to find by file path
                                            if deleted_count == 0:
                                                try:
                                                    # Look for vectors with file path in metadata
                                                    points = client.scroll(
                                                        collection_name=collection_name,
                                                        scroll_filter={
                                                            "must": [
                                                                {
                                                                    "key": "path",
                                                                    "match": {"value": record['path']}
                                                                }
                                                            ]
                                                        },
                                                        limit=1000,
                                                        with_payload=False,
                                                        with_vectors=False
                                                    )
                                                    
                                                    if points[0]:
                                                        point_ids = [point.id for point in points[0]]
                                                        if point_ids:
                                                            client.delete(
                                                                collection_name=collection_name,
                                                                points_selector=point_ids
                                                            )
                                                            deleted_count += len(point_ids)
                                                            st.success(f"✅ Deleted {len(point_ids)} vectors by file path")
                                                except Exception as e:
                                                    st.info(f"Strategy 2 (file path) failed: {str(e)}")
                                            
                                            # Strategy 3: Last resort - try to find vectors by content similarity
                                            if deleted_count == 0:
                                                try:
                                                    # Get a sample of the document content to search for similar vectors
                                                    file_path = None
                                                    if Path(record['path']).is_absolute():
                                                        file_path = Path(record['path'])
                                                    else:
                                                        possible_paths = [
                                                            proj_dir / record['path'],
                                                            proj_dir / "documents" / record['path'],
                                                            proj_dir / "documents" / Path(record['path']).name
                                                        ]
                                                        for path in possible_paths:
                                                            if path.exists():
                                                                file_path = path
                                                                break
                                                    
                                                    if file_path and file_path.exists():
                                                        with open(file_path, 'r', encoding='utf-8') as f:
                                                            content_sample = f.read()[:500]  # First 500 chars
                                                            
                                                        # Search for similar content
                                                        embeddings = OpenAIEmbeddings()
                                                        vectorstore = Qdrant(
                                                            client=client,
                                                            collection_name=collection_name,
                                                            embeddings=embeddings
                                                        )
                                                        
                                                        similar_docs = vectorstore.similarity_search(content_sample, k=10)
                                                        
                                                        # Find exact matches by comparing content
                                                        exact_matches = []
                                                        for doc in similar_docs:
                                                            if doc.page_content.startswith(content_sample[:100]):
                                                                exact_matches.append(doc)
                                                        
                                                        if exact_matches:
                                                            # Get point IDs for exact matches
                                                            points = client.scroll(
                                                                collection_name=collection_name,
                                                                scroll_filter={
                                                                    "must": [
                                                                        {
                                                                            "key": "page_content",
                                                                            "match": {"text": content_sample[:100]}
                                                                        }
                                                                    ]
                                                                },
                                                                limit=1000,
                                                                with_payload=False,
                                                                with_vectors=False
                                                            )
                                                            
                                                            if points[0]:
                                                                point_ids = [point.id for point in points[0]]
                                                                if point_ids:
                                                                    client.delete(
                                                                        collection_name=collection_name,
                                                                        points_selector=point_ids
                                                                    )
                                                                    deleted_count += len(point_ids)
                                                                    st.success(f"✅ Deleted {len(point_ids)} vectors by content similarity")
                                                except Exception as e:
                                                    st.info(f"Strategy 3 (content similarity) failed: {str(e)}")
                                            
                                            if deleted_count == 0:
                                                st.warning("⚠️ No vectors were found to delete. The document may not have been properly embedded.")
                                            else:
                                                st.success(f"✅ Successfully deleted {deleted_count} vectors from the collection")
                                       
                                    except Exception as e:
                                        st.error(f"⚠️ Document deleted from database but failed to remove vectors: {str(e)}")
                                        st.info("You may need to manually clean up the vector store.")
                                
                                st.success(f"✅ Document '{Path(record['path']).name}' deleted successfully!")
                                
                                # Clear session state
                                st.session_state[f"confirm_delete_{doc_key}"] = False
                                st.session_state[f"show_details_{doc_key}"] = False
                                
                                # Rerun to refresh the list
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Failed to delete document: {str(e)}")
                    
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{doc_key}"):
                            st.session_state[f"confirm_delete_{doc_key}"] = False
                    
                    with col3:
                        st.write("")  # Empty column for spacing
        
        # Bulk actions
        st.subheader("⚡ Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh List"):
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete All Pending"):
                if st.checkbox("I understand this will delete all pending documents"):
                    pending_docs = [doc for doc in all_documents if doc[8] == "pending"]
                    if pending_docs:
                        try:
                            for doc in pending_docs:
                                delete_document(con, doc[7])  # content_hash is at index 7
                            st.success(f"✅ Deleted {len(pending_docs)} pending documents!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete some documents: {str(e)}")
                    else:
                        st.info("No pending documents to delete.")
        
        with col3:
            if st.button("🧹 Clean Vector Store"):
                if st.checkbox("I understand this will attempt to clean orphaned vectors"):
                    try:
                        project_name = proj_dir.name
                        client = get_qdrant_client(project_name)
                        
                        if client.collection_exists(collection_name):
                            # Get all vectors in the collection
                            all_points = client.scroll(
                                collection_name=collection_name,
                                limit=10000,
                                with_payload=True,
                                with_vectors=False
                            )
                            
                            if all_points[0]:
                                orphaned_count = 0
                                for point in all_points[0]:
                                    if point.payload:
                                        # Check if this vector has a content_hash that exists in our database
                                        content_hash = point.payload.get('content_hash')
                                        if content_hash:
                                            # Check if document still exists in database
                                            doc_exists = con.execute(
                                                "SELECT 1 FROM documents WHERE content_hash = ?", 
                                                (content_hash,)
                                            ).fetchone()
                                            
                                            if not doc_exists:
                                                # This vector is orphaned, delete it
                                                client.delete(
                                                    collection_name=collection_name,
                                                    points_selector=[point.id]
                                                )
                                                orphaned_count += 1
                                
                                if orphaned_count > 0:
                                    st.success(f"✅ Cleaned {orphaned_count} orphaned vectors from collection")
                                else:
                                    st.info("✅ No orphaned vectors found")
                            else:
                                st.info("No vectors found in collection")
                        else:
                            st.warning("Collection does not exist")
                            
                    except Exception as e:
                        st.error(f"Failed to clean vector store: {str(e)}")
    
    except Exception as e:
        st.error(f"Failed to load documents: {str(e)}")
        st.info("Check your database connection and try again.")
