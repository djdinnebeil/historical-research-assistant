import json
from pathlib import Path

# Load metadata.json once at startup
def load_report_metadata(file_path: Path) -> dict:
    """Load metadata.json from the reports folder containing the file."""
    meta_file = file_path.parent / "metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f).get("reports", {})
    return {}


def parse_report(file_path: str) -> dict:
    """Parse a report text file into structured output."""
    path = Path(file_path)
    fname = path.stem  # filename without .txt

    # Look up metadata entry for this report
    REPORT_META = load_report_metadata(path)
    entry = REPORT_META.get(fname, {})

    raw_text = path.read_text(encoding="utf-8").strip()

    # Build citation fallback if missing
    citation = entry.get("citation")
    if not citation:
        citation = f'Report, {fname}'

    return {
        "page_content": raw_text,
        "metadata": {
            "source_type": "report",
            "source_id": fname,
            "title": entry.get("title"),
            "coverage_years": entry.get("coverage_years"),
            "publication_year": entry.get("publication_year"),
            "date": entry.get("publication_year"),
            "pages": entry.get("pages"),
            "file_path": str(file_path),
            "citation": citation
        }
    }
