import re
from typing import Dict, List
from docx import Document

PLACEHOLDER_PATTERNS = [
    r"\[[^\]]+\]",     # [PLACEHOLDER]
    r"\{\{[^}]+\}\}",  # {{PLACEHOLDER}}
    r"<[^>]+>",        # <PLACEHOLDER>
    r"_{3,}",          # _____
]

def extract_placeholders(file_path: str) -> Dict:
    doc = Document(file_path)

    # Join all paragraphs (simple, fast)
    lines: List[str] = [p.text for p in doc.paragraphs]
    text = "\n".join(lines)

    # Find placeholders
    raw_matches: List[str] = []
    for pattern in PLACEHOLDER_PATTERNS:
        raw_matches.extend(re.findall(pattern, text))

    # Normalize names (strip wrappers / underscores)
    cleaned = [m.strip("[]{}<>_ ").upper() for m in raw_matches]

    return {
        "text_preview": text[:500] + ("..." if len(text) > 500 else ""),
        "placeholders": sorted(set(cleaned)),
    }
