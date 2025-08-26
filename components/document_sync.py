import streamlit as st
from pathlib import Path
import hashlib
from db import document_exists, insert_document, update_document_status
from text_parsers.unified_parser import parse_file
from local_qdrant import adaptive_chunk_documents
from embedder import embed_documents
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
    
    # Scan documents folder
    with st.spinner("Scanning documents folder..."):
        text_files = scan_documents_folder(proj_dir)
    
    if not text_files:
        st.info("No text files found in the documents folder.")
        return
    
    st.write(f"Found {len(text_files)} text file(s) in the documents folder.")
    
    # Check which files are new or changed
    new_files = []
    existing_files = []
    
    for file_info in text_files:
        if document_exists(con, file_info['hash']):
            existing_files.append(file_info)
        else:
            new_files.append(file_info)
    
    st.write(f"📁 New files to process: {len(new_files)}")
    st.write(f"✅ Already processed: {len(existing_files)}")
    
    if not new_files:
        st.success("All documents are already synced!")
        return
    
    # Show new files
    st.subheader("📋 New Files to Process")
    for file_info in new_files:
        st.write(f"• {file_info['path'].name} ({file_info['size']} bytes)")
    
    # Start processing with batching
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    processed_count = 0
    errors = []
    
    # Initialize batching
    from local_qdrant import BATCH_SIZE
    staging_buffer = []
    batch_count = 0
    
    # Track chunk counts for each document
    document_chunk_counts = {}
    
    st.info(f"📦 Using batch processing with batch size: {BATCH_SIZE}")
    
    for i, file_info in enumerate(new_files):
        try:
            file_path = file_info['path']
            file_hash = file_info['hash']
            
            # Update progress
            progress = (i + 1) / len(new_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing {file_path.name}... ({i+1}/{len(new_files)})")
            
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
                
                # Store the chunk count for this document
                document_chunk_counts[file_hash] = len(chunked_docs)
                
                # Update database with chunk count
                update_document_status(con, file_hash, len(chunked_docs), "pending")
                
                # Add content_hash to metadata for tracking
                for chunk in chunked_docs:
                    if chunk.metadata is None:
                        chunk.metadata = {}
                    chunk.metadata['content_hash'] = file_hash
                
                # Add chunks to staging buffer
                staging_buffer.extend(chunked_docs)
                st.write(f"  📄 Added {len(chunked_docs)} chunks to batch (total: {len(staging_buffer)})")
                
                # Flush batch if it's full
                if len(staging_buffer) >= BATCH_SIZE:
                    st.write(f"  🚀 Flushing batch of {len(staging_buffer)} chunks...")
                    try:
                        # Embed and add to vector store
                        embed_documents(
                            staging_buffer, 
                            proj_dir.name, 
                            collection_name
                        )
                        
                        # Mark all documents in this batch as embedded with their correct chunk counts
                        for chunk in staging_buffer:
                            chunk_hash = chunk.metadata.get('content_hash')
                            if chunk_hash and chunk_hash in document_chunk_counts:
                                update_document_status(con, chunk_hash, document_chunk_counts[chunk_hash], "embedded")
                        
                        con.commit()
                        batch_count += 1
                        st.success(f"  ✅ Batch {batch_count} processed: {len(staging_buffer)} chunks")
                        
                    except Exception as e:
                        st.error(f"  ❌ Batch processing failed: {e}")
                        errors.append(f"Batch processing error: {e}")
                        # Mark documents as error
                        for chunk in staging_buffer:
                            chunk_hash = chunk.metadata.get('content_hash')
                            if chunk_hash:
                                update_document_status(con, chunk_hash, 0, "error")
                    
                    # Clear the buffer
                    staging_buffer.clear()
                
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
    
    # Final flush of remaining chunks
    if staging_buffer:
        st.write(f"  🚀 Flushing final batch of {len(staging_buffer)} chunks...")
        try:
            embed_documents(
                staging_buffer, 
                proj_dir.name, 
                collection_name
            )
            
            # Mark remaining documents as embedded with their correct chunk counts
            for chunk in staging_buffer:
                chunk_hash = chunk.metadata.get('content_hash')
                if chunk_hash and chunk_hash in document_chunk_counts:
                    update_document_status(con, chunk_hash, document_chunk_counts[chunk_hash], "embedded")
            
            con.commit()
            batch_count += 1
            st.success(f"  ✅ Final batch processed: {len(staging_buffer)} chunks")
            
        except Exception as e:
            st.error(f"  ❌ Final batch processing failed: {e}")
            errors.append(f"Final batch processing error: {e}")
            # Mark documents as error
            for chunk in staging_buffer:
                chunk_hash = chunk.metadata.get('content_hash')
                if chunk_hash:
                    update_document_status(con, chunk_hash, 0, "error")
    
    # Final status
    progress_bar.progress(1.0)
    status_text.text("Sync complete!")
    
    if processed_count > 0:
        st.success(f"✅ Successfully processed {processed_count} document(s) in {batch_count} batch(es)")
    
    if errors:
        st.error(f"❌ {len(errors)} error(s) occurred:")
        for error in errors:
            st.write(f"• {error}")
    
    # Show final database state
    st.subheader("📊 Final Database State")
    from db import list_documents_by_status
    final_pending = list_documents_by_status(con, "pending")
    final_embedded = list_documents_by_status(con, "embedded")
    final_error = list_documents_by_status(con, "error")
    
    st.write(f"Pending documents: {len(final_pending)}")
    st.write(f"Embedded documents: {len(final_embedded)}")
    st.write(f"Error documents: {len(final_error)}")
    
    if final_error:
        st.warning("Some documents had errors during processing. Check the error logs above.")

def render_document_sync(proj_dir: Path, con, collection_name: str):
    """Main render function for the document sync component."""
    st.subheader("🔄 Document Sync")
    st.write("This tool will scan your project's documents folder and automatically sync any new or changed documents to the database and vector store.")
    
    # Show current documents folder structure
    documents_dir = proj_dir / "documents"
    if documents_dir.exists():
        st.write(f"**Documents folder:** `{documents_dir}`")
        
        # Count files by type
        txt_files = list(documents_dir.rglob("*.txt"))
        st.write(f"**Text files found:** {len(txt_files)}")
        
        if txt_files:
            st.write("**File structure:**")
            for file_path in sorted(txt_files):
                relative_path = file_path.relative_to(documents_dir)
                st.write(f"• `{relative_path}`")
    else:
        st.warning("Documents folder not found. Please create it first.")
        return
    
    # Sync button
    if st.button("🔄 Sync Documents"):
        sync_documents(proj_dir, con, collection_name)
