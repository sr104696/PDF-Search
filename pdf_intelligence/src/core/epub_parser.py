try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    ebooklib = None
    BeautifulSoup = None

def extract_text_from_epub(file_path: str) -> list[dict]:
    """
    Extracts text from an EPUB file.
    Returns a list of dicts: [{'page_num': 1, 'text': '...'}, ...]
    Here 'page_num' refers to document parts/chapters.
    """
    if ebooklib is None or BeautifulSoup is None:
        raise ImportError("ebooklib or BeautifulSoup is not installed. Cannot parse EPUB.")

    book = epub.read_epub(file_path)
    pages_data = []

    chapter_num = 1
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            if text:
                pages_data.append({
                    "page_num": chapter_num,
                    "text": text
                })
                chapter_num += 1

    return pages_data
