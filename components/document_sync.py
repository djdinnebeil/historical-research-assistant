import streamlit as st
from pathlib import Path
import hashlib
from core import document_exists, insert_document, update_document_status, adaptive_chunk_documents, embed_documents, DocumentBatchProcessor, list_documents_by_status
from components.text_parsers.unified_parser import parse_file
from langchain.schema import Document

def get_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash for file content."""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def scan_documents_folder(proj_dir: Path):
    """Scan the documents folder and return all text files with their hashes."""
    documents_dir = proj_dir / "documents"
    if not documents_dir.exists():
        return []
    
    text_files = []
    for file_path in documents_dir.rglob("*.txt"):
        try:
            file_hash = get_file_hash(file_path)
            text_files.append({
                'path': file_path,
                'hash': file_hash,
                'size': file_path.stat().st_size
            })
        except Exception as e:
            st.warning(f"Could not process {file_path}: {e}")
    
    return text_files

def sync_documents(proj_dir: Path, con, collection_name: str):
    """Sync documents from the documents folder to the database and vector store."""
    st.subheader("🔄 Document Sync")
    
    # Check for pending documents first
    pending_docs = list_documents_by_status(con, "pending")
    # st.write(f"Found {len(pending_docs)} pending document(s).")
    # st.write(f"📋 Pending documents to process: {len(pending_docs)}")
    
    # Scan documents folder
    with st.spinner("Scanning documents folder..."):
        text_files = scan_documents_folder(proj_dir)
    
    if not text_files and not pending_docs:
        st.info("No text files found in the documents folder and no pending documents to process.")
        return
    
    if text_files:
        # st.write(f"Found {len(text_files)} text file(s) in the documents folder.")
        
        # Check which files are new or changed
        new_files = []
        existing_files = []
        
        for file_info in text_files:
            if document_exists(con, file_info['hash']):
                existing_files.append(file_info)
            else:
                new_files.append(file_info)
        
        # st.write(f"📁 New files to process: {len(new_files)}")
        # st.write(f"✅ Already processed: {len(existing_files)}")
    else:
        new_files = []
        existing_files = []
        st.write("No new files found in the documents folder.")
    
    if not new_files and not pending_docs:
        st.success("All documents are already synced!")
        return
    
    # Show new files
    if new_files:
        st.subheader("📋 New Files to Process")
        for file_info in new_files:
            st.write(f"• {file_info['path'].name} ({file_info['size']} bytes)")
    
    # Show pending documents
    if pending_docs:
        st.subheader("📋 Pending Documents to Process")
        for row in pending_docs:
            path = row[1]  # path is at index 1
            st.write(f"• {path}")
    
    # Calculate total items to process
    total_items = len(new_files) + len(pending_docs)
    
    # Start processing with batching
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    processed_count = 0
    errors = []
    
    # Initialize batch processor
    from core.vector_store import BATCH_SIZE
    batch_processor = DocumentBatchProcessor(BATCH_SIZE, proj_dir.name, collection_name)
    
    st.info(f"📦 Using batch processing with batch size: {BATCH_SIZE}")
    
    # Process new files first
    for i, file_info in enumerate(new_files):
        try:
            file_path = file_info['path']
            file_hash = file_info['hash']
            
            # Update progress
            progress = (i + 1) / total_items
            progress_bar.progress(progress)
            status_text.text(f"Processing new file {file_path.name}... ({i+1}/{total_items})")
            
            # Parse the file
            try:
                parsed = parse_file(str(file_path))
            except Exception as e:
                st.error(f"Failed to parse {file_path.name}: {e}")
                errors.append(f"Parse error in {file_path.name}: {e}")
                continue
            
            # Add to database
            try:
                insert_document(con, file_path, parsed, file_hash, 0)
                con.commit()
            except Exception as e:
                st.error(f"Failed to insert {file_path.name} into database: {e}")
                errors.append(f"Database error for {file_path.name}: {e}")
                continue
            
            # Process for vector store
            try:
                # Create Document objects for LangChain
                docs = [Document(
                    page_content=parsed['page_content'],
                    metadata=parsed['metadata']
                )]
                
                # Chunk the documents
                chunked_docs = adaptive_chunk_documents(docs)
                
                # Update database with chunk count and pending status
                update_document_status(con, file_hash, len(chunked_docs), "pending")
                
                # Add document chunks to batch processor
                updates = batch_processor.add_document(chunked_docs, file_hash, len(chunked_docs))
                st.write(f"  📄 Added {len(chunked_docs)} chunks to batch (total: {batch_processor.get_buffer_size()})")
                
                # Process any database updates if batch was flushed
                if updates:
                    st.write(f"  🚀 Batch flushed with {len(updates)} document updates")
                    try:
                        for chunk_hash, chunk_count in updates:
                            update_document_status(con, chunk_hash, chunk_count, "embedded")
                        con.commit()
                        st.success(f"  ✅ Batch {batch_processor.get_batch_count()} processed successfully")
                    except Exception as e:
                        st.error(f"  ❌ Database update failed: {e}")
                        errors.append(f"Database update error: {e}")
                        # Mark documents as error
                        for chunk_hash, chunk_count in updates:
                            update_document_status(con, chunk_hash, 0, "error")
                
                processed_count += 1
                
            except Exception as e:
                st.error(f"Failed to process {file_path.name} for vector store: {e}")
                errors.append(f"Vector store error for {file_path.name}: {e}")
                # Mark as error in database
                update_document_status(con, file_hash, 0, "error")
                continue
            
        except Exception as e:
            st.error(f"Unexpected error processing {file_info['path'].name}: {e}")
            errors.append(f"Unexpected error for {file_info['path'].name}: {e}")
    
    # Process pending documents
    for i, row in enumerate(pending_docs):
        try:
            # Extract row data - content_hash is at index 6, not 5
            path, citation, source_type, source_id, date, num_chunks, content_hash, status, added_at = row[1:10]
            
            # Update progress
            progress = (len(new_files) + i + 1) / total_items
            progress_bar.progress(progress)
            status_text.text(f"Processing pending document {path}... ({len(new_files) + i + 1}/{total_items})")
            
            # Parse the file
            file_path = proj_dir / "documents" / path
            if not file_path.exists():
                st.error(f"❌ File not found: {file_path}")
                errors.append(f"File not found: {file_path}")
                continue
            
            try:
                parsed = parse_file(str(file_path))
            except Exception as e:
                st.error(f"Failed to parse {path}: {e}")
                errors.append(f"Parse error in {path}: {e}")
                continue
            
            # Process for vector store
            try:
                # Create Document objects for LangChain
                docs = [Document(
                    page_content=parsed['page_content'],
                    metadata=parsed['metadata']
                )]
                
                # Chunk the documents
                chunked_docs = adaptive_chunk_documents(docs)
                
                # Add document chunks to batch processor
                updates = batch_processor.add_document(chunked_docs, content_hash, len(chunked_docs))
                st.write(f"  📄 Added {len(chunked_docs)} chunks to batch (total: {batch_processor.get_buffer_size()})")
                
                # Process any database updates if batch was flushed
                if updates:
                    st.write(f"  🚀 Batch flushed with {len(updates)} document updates")
                    try:
                        for chunk_hash, chunk_count in updates:
                            update_document_status(con, chunk_hash, chunk_count, "embedded")
                        con.commit()
                        st.success(f"  ✅ Batch {batch_processor.get_batch_count()} processed successfully")
                    except Exception as e:
                        st.error(f"  ❌ Database update failed: {e}")
                        errors.append(f"Database update error: {e}")
                        # Mark documents as error
                        for chunk_hash, chunk_count in updates:
                            update_document_status(con, chunk_hash, 0, "error")
                
                processed_count += 1
                
            except Exception as e:
                st.error(f"Failed to process {path} for vector store: {e}")
                errors.append(f"Vector store error for {path}: {e}")
                # Mark as error in database
                update_document_status(con, content_hash, 0, "error")
                continue
            
        except Exception as e:
            st.error(f"Unexpected error processing pending document {row[1] if len(row) > 1 else 'unknown'}: {e}")
            errors.append(f"Unexpected error for pending document: {e}")
    
    # Final flush of remaining chunks
    final_updates = batch_processor.finalize()
    if final_updates:
        st.write(f"  🚀 Flushing final batch with {len(final_updates)} document updates...")
        try:
            for chunk_hash, chunk_count in final_updates:
                update_document_status(con, chunk_hash, chunk_count, "embedded")
            con.commit()
            st.success(f"  ✅ Final batch processed successfully")
        except Exception as e:
            st.error(f"  ❌ Final batch processing failed: {e}")
            errors.append(f"Final batch processing error: {e}")
            # Mark documents as error
            for chunk_hash, chunk_count in final_updates:
                update_document_status(con, chunk_hash, 0, "error")
    
    # Final status
    progress_bar.progress(1.0)
    status_text.text("Sync complete!")
    
    if processed_count > 0:
        st.success(f"✅ Successfully processed {processed_count} document(s) in {batch_processor.get_batch_count()} batch(es)")
        if new_files and pending_docs:
            st.info(f"📊 Processed {len(new_files)} new files and {len(pending_docs)} pending documents")
        elif new_files:
            st.info(f"📊 Processed {len(new_files)} new files")
        elif pending_docs:
            st.info(f"📊 Processed {len(pending_docs)} pending documents")
    
    if errors:
        st.error(f"❌ {len(errors)} error(s) occurred:")
        for error in errors:
            st.write(f"• {error}")
    
    # Show final database state
    st.subheader("📊 Final Database State")
    final_pending = list_documents_by_status(con, "pending")
    final_embedded = list_documents_by_status(con, "embedded")
    final_error = list_documents_by_status(con, "error")
    
    st.write(f"Pending documents: {len(final_pending)}")
    st.write(f"Embedded documents: {len(final_embedded)}")
    st.write(f"Error documents: {len(final_error)}")
    
    if final_error:
        st.warning("Some documents had errors during processing. Check the error logs above.")
    
    # Show summary of what was processed
    if new_files or pending_docs:
        st.subheader("📋 Processing Summary")
        if new_files:
            st.write(f"• New files processed: {len(new_files)}")
        if pending_docs:
            st.write(f"• Pending documents processed: {len(pending_docs)}")
        st.write(f"• Total documents processed: {processed_count}")
        st.write(f"• Batches used: {batch_processor.get_batch_count()}")

def render_document_sync(proj_dir: Path, con, collection_name: str):
    """Main render function for the document sync component."""
    st.subheader("🔄 Document Sync")
    st.write("This tool will scan your project's documents folder and automatically sync any new or changed documents to the database and vector store. It will also process any documents with 'pending' status.")
    
    # Show current documents folder structure
    documents_dir = proj_dir / "documents"
    if documents_dir.exists():
        st.write(f"**Documents folder:** `{documents_dir}`")
        
        # Count files by type
        txt_files = list(documents_dir.rglob("*.txt"))
        st.write(f"**Text files found:** {len(txt_files)}")
        
        text_files = scan_documents_folder(proj_dir)
        new_files = []
        existing_files = []

        if text_files:            
            # Check which files are new or changed
            for file_info in text_files:
                if document_exists(con, file_info['hash']):
                    existing_files.append(file_info)
                else:
                    new_files.append(file_info)
        
        st.write(f"New files to process: {len(new_files)}")

        pending_docs = list_documents_by_status(con, "pending")
        st.write(f"Pending documents found: {len(pending_docs)}")

        if new_files:
            st.write("**New files:**")
            for file_path in new_files:
                relative_path = file_path['path'].relative_to(documents_dir)
                st.write(f"• `{relative_path}`")

                # st.write(file_path)
                # relative_path = file_path.relative_to(documents_dir)
                # st.write(f"• `{relative_path}`")

        if pending_docs:
            st.write("**Pending documents structure:**")
            for file_path in pending_docs:
                print(file_path)
                st.write(f"• `{file_path[1]}`")
                # relative_path = file_path.relative_to(documents_dir)
                # st.write(f"• `{relative_path}`")

        # if txt_files:
        #     st.write("**File structure:**")
        #     for file_path in sorted(txt_files):
        #         relative_path = file_path.relative_to(documents_dir)
        #         st.write(f"• `{relative_path}`")
    else:
        st.warning("Documents folder not found. Please create it first.")
        return
    
    # Sync button
    if st.button("🔄 Sync Documents"):
        sync_documents(proj_dir, con, collection_name)
