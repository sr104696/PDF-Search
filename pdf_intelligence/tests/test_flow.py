import os
import sys

# Ensure src is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.index.indexer import index_file
from src.search.searcher import execute_search
from src.index.schema import initialize_db

def create_dummy_pdf(path):
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path)
    c.drawString(100, 750, "This is a test document about Python programming and offline search.")
    c.drawString(100, 730, "We are testing the BM25 algorithm and sqlite FTS5 integration.")
    c.showPage()
    c.save()

def main():
    print("Initializing DB...")
    initialize_db()

    test_pdf_path = "test_doc.pdf"
    print(f"Creating dummy PDF at {test_pdf_path}...")
    try:
        import reportlab
        create_dummy_pdf(test_pdf_path)
    except ImportError:
        print("reportlab not installed, skipping PDF creation and testing with plain text instead.")
        return

    print(f"Indexing {test_pdf_path}...")
    try:
        index_file(test_pdf_path)
        print("Indexing successful.")
    except Exception as e:
        print(f"Error during indexing: {e}")
        return

    print("\nExecuting Search for 'Python'...")
    results = execute_search("Python")
    if results:
        for r in results:
            print(f"Match: {r['title']} | Score: {r['score']}")
            print(f"Snippet: {r['snippet']}")
    else:
        print("No results found.")

    print("\nExecuting Search for 'offline algorithm'...")
    results = execute_search("offline algorithm")
    if results:
        for r in results:
            print(f"Match: {r['title']} | Score: {r['score']}")
            print(f"Snippet: {r['snippet']}")
    else:
        print("No results found.")

    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)

if __name__ == "__main__":
    main()
