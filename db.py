import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

# Global, must be set by set_project_db()
DB_PATH: Path | None = None
PROJECTS_DIR = Path("projects")

def file_sha256_from_buffer(buffer) -> str:
    h = hashlib.sha256()
    h.update(buffer)
    return h.hexdigest()

def file_sha256(path: Path) -> str:
    """Compute SHA256 hash for file content."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def set_project_db(project_name: str):
    """
    Set the DB_PATH based on project_name.
    Database will be stored at: projects/{project_name}/{project_name}.sqlite
    """
    global DB_PATH
    proj_dir = PROJECTS_DIR / project_name
    proj_dir.mkdir(parents=True, exist_ok=True)
    DB_PATH = proj_dir / f"{project_name}.sqlite"

def ensure_db():
    """Ensure the database exists and has the correct schema."""
    if DB_PATH is None:
        raise RuntimeError("DB_PATH is not set. Call set_project_db() first.")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        path         TEXT,
        citation     TEXT,
        source_type  TEXT,
        source_id    TEXT,
        date         TEXT,
        num_chunks   INTEGER,
        content_hash TEXT UNIQUE,
        status       TEXT DEFAULT 'pending',   -- NEW FIELD
        added_at     DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    return con


def document_exists(con, content_hash: str) -> bool:
    cur = con.execute("SELECT 1 FROM documents WHERE content_hash = ?", (content_hash,))
    return cur.fetchone() is not None

def insert_document(con, path: Path, parsed: dict, content_hash: str, num_chunks: int) -> None:
    """Insert a new document record with its metadata + chunk count."""
    md = parsed['metadata']
    con.execute("""
    INSERT INTO documents (path, citation, source_type, source_id, date, content_hash, num_chunks, status, added_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(path),
        md.get('citation'),
        md.get('source_type'),
        md.get('source_id'),
        md.get('date'),
        content_hash,
        num_chunks,
        'pending',
        datetime.utcnow().isoformat()
    ))

def update_document_status(con, content_hash: str, num_chunks: int, status: str = "embedded") -> None:
    """Update chunk count and status for a document after processing."""
    con.execute(
        "UPDATE documents SET num_chunks=?, status=? WHERE content_hash=?",
        (num_chunks, status, content_hash),
    )
    con.commit()


def delete_document(con, content_hash: str) -> None:
    """Delete a document row by its content hash."""
    con.execute("DELETE FROM documents WHERE content_hash = ?", (content_hash,))
    con.commit()

def list_documents(con):
    """Return summary list of documents."""
    cur = con.execute(
        "SELECT path, citation, source_id, date, num_chunks, added_at "
        "FROM documents ORDER BY added_at DESC"
    )
    return cur.fetchall()

def list_all_documents(con):
    """Return all documents with full metadata."""
    cur = con.execute("SELECT * FROM documents ORDER BY added_at DESC")
    return cur.fetchall()

def list_documents_by_status(con, status: str):
    """Return all documents with the given status."""
    return con.execute(
        "SELECT * FROM documents WHERE status=? ORDER BY added_at DESC", 
        (status,)
    ).fetchall()



if __name__ == "__main__":
    set_project_db("demo_project")
    con = ensure_db()
    print(list_all_documents(con))
