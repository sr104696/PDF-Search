import os
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extracts text from a PDF file.
    Returns a list of dicts: [{'page_num': 1, 'text': '...'}, ...]
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is not installed. Cannot parse PDF.")

    pages_data = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_data.append({
                    "page_num": i + 1,
                    "text": text
                })
    return pages_data
