import streamlit as st
import json
from pathlib import Path
from db import file_sha256_from_buffer, insert_document, document_exists
from text_parsers.unified_parser import parse_file

def render_books_uploader(proj_dir: Path, con):
    st.subheader("📚 Upload a Book")
    books_dir = proj_dir / "documents" / "books"
    books_dir.mkdir(parents=True, exist_ok=True)

    existing_books = [p.name for p in books_dir.iterdir() if p.is_dir()]
    mode = st.radio("Select option", ["Create new book", "Use existing book"])

    folder_name = None
    if mode == "Create new book":
        folder_name = st.text_input("Enter new folder name (e.g. amatol_book)")
        if folder_name and st.button("Create Book Folder"):
            (books_dir / folder_name).mkdir(parents=True, exist_ok=True)
            st.success(f"📂 Created folder: {folder_name}")
    else:
        folder_name = st.selectbox("Select existing book", existing_books)

    if not folder_name:
        return

    book_dir = books_dir / folder_name

    # Step 2: Prompt for metadata.json
    meta_file = book_dir / "metadata.json"
    if not meta_file.exists():
        st.info("No metadata.json found. Let's create one.")
        title = st.text_input("Book title")
        year = st.number_input("Year", min_value=0, max_value=2100, value=1918)
        citation_format = st.text_input("Citation format", value="{title}, {year}, {page}, {section}")
        if st.button("Save Metadata"):
            data = {
                "source_type": "book",
                "source_id": folder_name,
                "title": title,
                "year": year,
                "citation_format": citation_format
            }
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            st.success(f"✅ metadata.json created for {folder_name}")
    else:
        st.success("📑 metadata.json already exists")

    # Step 3: Upload text files for this book
    uploaded_files = st.file_uploader(
        f"Upload pages/sections into {folder_name}",
        accept_multiple_files=True,
        type=["txt"]
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Compute hash from buffer BEFORE saving
            file_bytes = uploaded_file.getbuffer()
            h = file_sha256_from_buffer(file_bytes)

            if document_exists(con, h):
                st.warning(f"⚠️ {uploaded_file.name} has already been uploaded (duplicate). Skipping.")
                continue

            # Save only if unique
            save_path = book_dir / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(file_bytes)
            st.success(f"✅ Saved {uploaded_file.name} to {book_dir}")

            # Insert into DB
            rel_path = f"books/{folder_name}/{uploaded_file.name}"
            parsed = parse_file(str(save_path))
            insert_document(con, rel_path, parsed, h, num_chunks=0)
            con.commit()
            st.info(f"📥 Added {uploaded_file.name} to DB (status: pending)")