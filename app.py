import streamlit as st
from components.sidebar import render_sidebar
from components.uploader import render_uploader
from components.pending_list import render_pending_list
from components.process_pending import render_process_pending
from components.vector_store_viewer import render_vector_store_viewer
from components.document_manager import render_document_manager
from components.qa_interface import render_qa_interface

st.title("📜 Historical Research Assistant")

selected, proj_dir, db_client, nav_choice = render_sidebar()

if db_client:
    con, client = db_client
    collection_name = st.session_state.get("collection_name", f"{selected}_docs")

    if nav_choice == "Uploader":
        render_uploader(proj_dir, con)
    elif nav_choice == "Pending Documents":
        render_pending_list(con)
    elif nav_choice == "Process Pending":
        render_process_pending(proj_dir, con, proj_dir / "qdrant", collection_name)
    elif nav_choice == "Vector Store":
        render_vector_store_viewer(proj_dir, proj_dir / "qdrant", collection_name)
    elif nav_choice == "Document Manager":
        render_document_manager(proj_dir, con, collection_name)
    elif nav_choice == "Ask Questions":
        render_qa_interface(selected, collection_name)
