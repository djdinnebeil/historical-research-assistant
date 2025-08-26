import streamlit as st
from pathlib import Path
from db import ensure_db, set_project_db
from local_qdrant import get_qdrant_client, clear_qdrant_cache

PROJECTS_DIR = Path("projects")

def list_projects():
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir()
    return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]

def render_sidebar():
    projects = list_projects()

    # --- Manage session state for selected project ---
    if "selected_project" not in st.session_state:
        st.session_state["selected_project"] = "-- New Project --"

    options = ["-- New Project --"] + projects
    selected = st.sidebar.selectbox(
        "Select a project",
        options,
        index=options.index(st.session_state["selected_project"]) 
              if st.session_state["selected_project"] in options else 0
    )
    
    # Clear Qdrant cache when switching projects to avoid stale connections
    if selected != st.session_state["selected_project"] and st.session_state["selected_project"] != "-- New Project --":
        clear_qdrant_cache()
        st.info(f"🔄 Switched from {st.session_state['selected_project']} to {selected}")

    if selected == "-- New Project --":
        new_name = st.sidebar.text_input("New project name")
        collection_name = st.sidebar.text_input("Vector collection name", value=f"{new_name}_docs")

        if st.sidebar.button("Create Project"):
            proj_dir = PROJECTS_DIR / new_name
            if proj_dir.exists():
                st.error("Project already exists!")
            else:
                (proj_dir / "qdrant").mkdir(parents=True)
                (proj_dir / "documents").mkdir(parents=True)
                set_project_db(new_name)
                ensure_db()
                st.success(f"Created project {new_name}")

                # Save collection name
                st.session_state["collection_name"] = collection_name
                st.session_state["selected_project"] = new_name
                st.rerun()

        return None, None, None, None


    # --- Navigation menu ---
    nav_choice = st.sidebar.radio(
        "Navigation",
        ["Uploader", "Pending Documents", "Process Pending", "Vector Store", "Document Manager", "Ask Questions"]
    )

    proj_dir = PROJECTS_DIR / selected
    set_project_db(selected)
    con = ensure_db()
    client = get_qdrant_client(selected)
    st.success(f"Loaded project {selected}")
    st.session_state["selected_project"] = selected

    # Default collection name if not set
    if "collection_name" not in st.session_state:
        st.session_state["collection_name"] = f"{selected}_docs"

    return selected, proj_dir, (con, client), nav_choice
