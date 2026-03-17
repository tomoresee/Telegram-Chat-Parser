import os
from datetime import datetime


EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")


def save_to_file(content: str) -> str:
    """Сохраняет текст в папку exports/export_ГГГГММДД_ЧЧММСС.txt."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{timestamp}.txt"
    filepath = os.path.join(EXPORT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
