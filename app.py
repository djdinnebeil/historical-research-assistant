import streamlit as st
from components.sidebar import render_sidebar
from components.uploader import render_uploader
from components.pending_list import render_pending_list
from components.process_pending import render_process_pending
from components.document_sync import render_document_sync
from components.vector_store_viewer import render_vector_store_viewer
from components.document_manager import render_document_manager
from components.qa_interface import render_qa_interface
from components.chat_history_viewer import render_chat_history_viewer
from components.project_manager import render_project_manager

# Clean up any stale Qdrant connections on app start
if "qdrant_initialized" not in st.session_state:
    from local_qdrant import clear_qdrant_cache
    clear_qdrant_cache()
    st.session_state["qdrant_initialized"] = True

st.title("📜 Historical Research Assistant")

selected, proj_dir, db_client, nav_choice = render_sidebar()

# Debug info - show current project and collection name (AFTER sidebar processing)
if "selected_project" in st.session_state and st.session_state["selected_project"] != "-- New Project --":
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📁 Current Project: **{st.session_state['selected_project']}**")
    with col2:
        collection_name = st.session_state.get("collection_name", "Not set")
        st.info(f"🗂️ Collection: **{collection_name}**")
    
    # Show project change counter for debugging
    if "project_change_counter" in st.session_state:
        print(f"Project changes: {st.session_state['project_change_counter']}")

# Ensure the session state is properly set for the selected project
if selected != "-- New Project --":
    st.session_state["selected_project"] = selected
    st.session_state["collection_name"] = f"{selected}_docs"

# Simplified project change detection - compare with the actual selected project from sidebar
if "last_selected_project" not in st.session_state:
    st.session_state["last_selected_project"] = selected
    st.session_state["project_change_counter"] = 0
elif st.session_state["last_selected_project"] != selected:
    # Project has changed - perform cleanup
    print(f"🔄 Project change detected: {st.session_state['last_selected_project']} → {selected}")
    print(f"🔄 Project changed from {st.session_state['last_selected_project']} to {selected}")
    
    # Clear old project data
    if "db_client" in st.session_state:
        print("🗑️ Clearing old db_client")
        del st.session_state["db_client"]
    
    # Clear Qdrant cache
    print("🗑️ Clearing Qdrant cache")
    from local_qdrant import force_clear_all_qdrant_caches
    force_clear_all_qdrant_caches()
    
    # Update tracking
    st.session_state["last_selected_project"] = selected
    st.session_state["project_change_counter"] = st.session_state.get("project_change_counter", 0) + 1
    print(f"🔄 Updated last_selected_project={st.session_state['last_selected_project']}, counter={st.session_state['project_change_counter']}")
    
    # Force a rerun to ensure clean state
    st.rerun()
else:
    print(f"✅ Same project, no change needed: {selected}")

# Navigation change detection
if "last_nav_choice" not in st.session_state:
    st.session_state["last_nav_choice"] = nav_choice
elif st.session_state["last_nav_choice"] != nav_choice:
    # Navigation has changed
    print(f"🔄 Navigation changed: {st.session_state['last_nav_choice']} → {nav_choice}")
    st.session_state["last_nav_choice"] = nav_choice
    
    # Force a rerun to ensure the new navigation section loads immediately
    st.rerun()

# Additional debugging
print(f"Debug: selected={selected}, last_selected_project={st.session_state.get('last_selected_project', 'None')}, db_client={db_client is not None}")

# More detailed debugging
if selected != "-- New Project --" and proj_dir is not None:
    print(f"Directory exists: {proj_dir.exists()}")
    print(f"Project details: {selected}")
    print(f"Navigation choice: {nav_choice}")
    print(f"DB client type: {type(db_client)}")
elif selected == "-- New Project --":
    print("No project selected - new project creation mode")
else:
    print(f"Project selected but proj_dir is None: {selected}")

# Ensure we have a valid project selected
if selected == "-- New Project --":
    st.warning("⚠️ Please select a project or create a new one to continue.")
    st.stop()

if db_client:
    con, client = db_client
    # Store database client in session state for components to use
    st.session_state.db_client = db_client
    collection_name = st.session_state.get("collection_name", f"{selected}_docs")

    if nav_choice == "Uploader":
        render_uploader(proj_dir, con)
    elif nav_choice == "Pending Documents":
        render_pending_list(con)
    elif nav_choice == "Process Pending":
        render_process_pending(proj_dir, con, proj_dir / "qdrant", collection_name)
    elif nav_choice == "Document Sync":
        render_document_sync(proj_dir, con, collection_name)
    elif nav_choice == "Vector Store":
        render_vector_store_viewer(proj_dir, proj_dir / "qdrant", collection_name)
    elif nav_choice == "Document Manager":
        render_document_manager(proj_dir, con, collection_name)
    elif nav_choice == "Ask Questions":
        render_qa_interface(selected, collection_name)
    elif nav_choice == "Chat History":
        render_chat_history_viewer(con, selected)
    elif nav_choice == "Project Management":
        render_project_manager(proj_dir, db_client, collection_name)
