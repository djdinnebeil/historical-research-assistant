from pathlib import Path
import streamlit as st
from db import ensure_db, set_project_db
from local_qdrant import get_qdrant_client
import shutil

PROJECTS_DIR = Path("projects")
DOC_TYPES = ["books", "journals", "newspapers", "reports", "web_articles", "unsorted"]

@st.cache_resource
def load_qdrant_client(project_name: str):
    return get_qdrant_client(project_name)

def list_projects():
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir()
    return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]

# --- Sidebar UI ---
projects = list_projects()
selected = st.sidebar.selectbox("Select a project", ["-- New Project --"] + projects)

if selected == "-- New Project --":
    new_name = st.sidebar.text_input("New project name")
    if st.sidebar.button("Create Project"):
        proj_dir = PROJECTS_DIR / new_name
        if proj_dir.exists():
            st.error("Project already exists!")
        else:
            (proj_dir / "qdrant").mkdir(parents=True)
            (proj_dir / "documents").mkdir(parents=True)
            # init DB
            set_project_db(new_name)
            ensure_db()
            st.success(f"Created project {new_name}")
else:
    st.success(f"Loaded project {selected}")
    proj_dir = PROJECTS_DIR / selected
    set_project_db(selected)
    con = ensure_db()
    client = load_qdrant_client(selected)

    # --- Upload Section ---
    st.header("📂 Upload Documents")

    uploaded_files = st.file_uploader(
        "Upload one or more files",
        accept_multiple_files=True,
        type=["txt", "pdf", "docx"]
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.subheader(f"File: {uploaded_file.name}")
            doc_type = st.selectbox(
                f"Select type for {uploaded_file.name}",
                DOC_TYPES,
                key=uploaded_file.name
            )

            if st.button(f"Save {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
                dest_dir = proj_dir / "documents" / doc_type
                dest_dir.mkdir(parents=True, exist_ok=True)

                save_path = dest_dir / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success(f"✅ Saved {uploaded_file.name} to {save_path}")
