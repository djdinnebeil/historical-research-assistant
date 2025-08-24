import shutil
from pathlib import Path

DOC_TYPES = ["books", "journals", "newspapers", "reports", "web_articles", "unsorted"]

def copy_files_to_project(project_name: str, file_paths: list[str]):
    """
    Copy one or more files into the correct project/documents/{type} folder.
    Prompts user for document type for each file.
    """
    project_dir = Path("projects") / project_name / "documents"
    project_dir.mkdir(parents=True, exist_ok=True)

    for file_path in file_paths:
        src = Path(file_path)
        if not src.exists():
            print(f"⚠️ Skipping: {file_path} (not found)")
            continue

        # Prompt user for doc type
        print(f"\nFile: {src.name}")
        for i, dtype in enumerate(DOC_TYPES, start=1):
            print(f"  {i}. {dtype}")
        choice = input("Select document type [1-6]: ").strip()

        try:
            dtype = DOC_TYPES[int(choice) - 1]
        except Exception:
            print("⚠️ Invalid choice, defaulting to 'unsorted'")
            dtype = "unsorted"

        dest_dir = project_dir / dtype
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name

        shutil.copy2(src, dest)
        print(f"✅ Copied {src.name} → {dest}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload documents into a project.")
    parser.add_argument("project", help="Project name")
    parser.add_argument("files", nargs="+", help="File(s) to upload")
    args = parser.parse_args()

    copy_files_to_project(args.project, args.files)
