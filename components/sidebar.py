import streamlit as st
from pathlib import Path
from db import ensure_db, set_project_db
from local_qdrant import get_qdrant_client, clear_qdrant_cache

# Use absolute path to avoid relative path resolution issues
PROJECTS_DIR = Path.cwd() / "projects"

def list_projects():
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir()
    return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]

def clear_project_session_state():
    """Clear all project-specific session state variables"""
    keys_to_clear = [
        "db_client", "qdrant_initialized",
        "show_details_", "show_delete_all", "delete_confirmation"
    ]
    
    # Clear specific keys
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear keys that start with specific prefixes
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith("show_details_")]
    for key in keys_to_remove:
        del st.session_state[key]

def render_sidebar():
    print("🔧 Sidebar: Starting render_sidebar function")
    projects = list_projects()
    print(f"🔧 Sidebar: Found projects: {projects}")

    # --- Manage session state for selected project ---
    if "selected_project" not in st.session_state:
        print("🔧 Sidebar: No selected_project in session state, setting to '-- New Project --'")
        st.session_state["selected_project"] = "-- New Project --"
    else:
        print(f"🔧 Sidebar: Current selected_project: {st.session_state['selected_project']}")
    
    # Initialize project change counter
    if "project_change_counter" not in st.session_state:
        print("🔧 Sidebar: No project_change_counter in session state, setting to 0")
        st.session_state["project_change_counter"] = 0
    else:
        print(f"🔧 Sidebar: Current project_change_counter: {st.session_state['project_change_counter']}")
    
    # Preserve navigation choice across project switches
    if "current_nav_choice" not in st.session_state:
        print("🔧 Sidebar: No current_nav_choice in session state, setting to 'Uploader'")
        st.session_state["current_nav_choice"] = "Uploader"
    else:
        print(f"🔧 Sidebar: Current current_nav_choice: {st.session_state['current_nav_choice']}")

    options = ["-- New Project --"] + projects
    print(f"🔧 Sidebar: Available options: {options}")
    
    selected = st.sidebar.selectbox(
        "Select a project",
        options,
        index=options.index(st.session_state["selected_project"]) 
              if st.session_state["selected_project"] in options else 0,
        key="project_select"
    )
    print(f"🔧 Sidebar: User selected: {selected}")
    
    # No project switching logic here - let the main app handle it
    # This prevents conflicts and race conditions
    
    # Validate that the selected project is valid
    if selected != "-- New Project --" and selected not in projects:
        print(f"🔧 Sidebar: ERROR - Project '{selected}' no longer available!")
        st.error(f"❌ Project '{selected}' is no longer available!")
        st.session_state["selected_project"] = "-- New Project --"
        clear_project_session_state()
        st.rerun()

    # Check if selected project still exists (in case it was deleted)
    if selected != "-- New Project --" and not (PROJECTS_DIR / selected).exists():
        print(f"🔧 Sidebar: ERROR - Project '{selected}' no longer exists!")
        st.error(f"❌ Project '{selected}' no longer exists!")
        st.session_state["selected_project"] = "-- New Project --"
        clear_project_session_state()
        st.rerun()

    if selected == "-- New Project --":
        print("🔧 Sidebar: New project creation mode")
        new_name = st.sidebar.text_input("New project name")
        collection_name = st.sidebar.text_input("Vector collection name", value=f"{new_name}_docs")

        if st.sidebar.button("Create Project"):
            print(f"🔧 Sidebar: Creating new project: {new_name}")
            proj_dir = PROJECTS_DIR / new_name
            if proj_dir.exists():
                st.error("Project already exists!")
            else:
                (proj_dir / "qdrant").mkdir(parents=True)
                (proj_dir / "documents").mkdir(parents=True)
                set_project_db(new_name)
                ensure_db()
                st.success(f"Created project {new_name}")

                # Save collection name and update selected project
                st.session_state["collection_name"] = collection_name
                st.session_state["selected_project"] = new_name
                st.rerun()

        return None, None, None, None

    # --- Navigation menu ---
    print(f"🔧 Sidebar: Setting up navigation for project: {selected}")
    
    # Define navigation options
    nav_options = ["Uploader", "Process Pending", "Document Sync", "Vector Store", "Document Manager", "Ask Questions", "Chat History", "Project Management"]
    
    # Safely get the current navigation choice index
    current_nav = st.session_state.get("current_nav_choice", "Uploader")
    try:
        nav_index = nav_options.index(current_nav)
    except ValueError:
        # If the stored choice is invalid, default to Uploader
        nav_index = 0
        st.session_state["current_nav_choice"] = "Uploader"
    
    nav_choice = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=nav_index,
        key=f"nav_radio_{selected}"  # Unique key per project to prevent conflicts
    )
    print(f"🔧 Sidebar: Navigation choice: {nav_choice}")
    
    # Update stored navigation choice immediately
    if nav_choice != st.session_state.get("current_nav_choice"):
        print(f"🔧 Sidebar: Navigation changed from {st.session_state.get('current_nav_choice', 'None')} to {nav_choice}")
        st.session_state["current_nav_choice"] = nav_choice

    print(f"🔧 Sidebar: Processing project: {selected}")
    proj_dir = PROJECTS_DIR / selected
    print(f"🔧 Sidebar: Project directory: {proj_dir}")
    print(f"🔧 Sidebar: Project directory exists: {proj_dir.exists()}")
    
    set_project_db(selected)
    print(f"🔧 Sidebar: Database set for project: {selected}")
    
    con = ensure_db()
    print(f"🔧 Sidebar: Database connection established: {con is not None}")
    
    print(f"🔧 Sidebar: Getting Qdrant client for project: {selected}")
    client = get_qdrant_client(selected)
    print(f"🔧 Sidebar: Qdrant client obtained: {client is not None}")
    
    st.success(f"Loaded project {selected}")
    print(f"🔧 Sidebar: Success message displayed for project: {selected}")
    
    # Update session state for the current project
    st.session_state["selected_project"] = selected
    st.session_state["collection_name"] = f"{selected}_docs"
    print(f"🔧 Sidebar: Session state updated: selected_project={selected}, collection_name={f'{selected}_docs'}")

    print(f"🔧 Sidebar: Returning values: selected={selected}, proj_dir={proj_dir}, db_client={con is not None}, nav_choice={nav_choice}")
    return selected, proj_dir, (con, client), nav_choice
