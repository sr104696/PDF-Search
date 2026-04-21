from setuptools import setup, find_packages

setup(
    name="pdf_intelligence",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pdfplumber",
        "snowballstemmer",
        "EbookLib",
        "beautifulsoup4"
    ],
    entry_points={
        "console_scripts": [
            "pdf_intelligence=src.main:main",
        ],
    },
)
