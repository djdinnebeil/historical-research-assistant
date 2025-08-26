import sys
from pathlib import Path

# Allow imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from text_parsers.book_parser import parse_book
from text_parsers.journal_parser import parse_journal_article
from text_parsers.newspaper_parser import parse_newspaper_article
from text_parsers.report_parser import parse_report
from text_parsers.web_article_parser import parse_web_article

# Dispatch table
DISPATCH = {
    "books": parse_book,
    "journals": parse_journal_article,
    "newspapers": parse_newspaper_article,
    "reports": parse_report,
    "web_articles": parse_web_article,
}

def parse_file(file_path: str) -> dict:
    """
    Unified parser that dispatches based on top-level folder.
    Returns a dict with keys: page_content, metadata.
    """
    path = Path(file_path)
    try:
        folder = path.parts[3]  # e.g., "journals" from "amatol/journals/..."
    except IndexError:
        raise ValueError(f"Unexpected file structure: {file_path}")

    parser = DISPATCH.get(folder)
    if not parser:
        raise ValueError(f"Unknown source type: {folder} for file {file_path}")
    return parser(file_path)


if __name__ == "__main__":
    root = Path("amatol")
    all_files = root.rglob("*.txt")

    with open("amatol_parsed.txt", "w", encoding="utf-8") as f:
        for file_path in all_files:
            parsed = parse_file(file_path)
            print("=== File:", file_path, "===", file=f)
            print("Page Content:\n", parsed["page_content"], sep="", file=f)
            print("\nMetadata:", file=f)
            for k, v in parsed["metadata"].items():
                print(f"  {k}: {v}", file=f)
            print(file=f)
