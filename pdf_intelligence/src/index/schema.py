import sqlite3
import os
from src.utils.constants import DB_PATH

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT,
            filePath TEXT UNIQUE,
            pageCount INTEGER,
            indexedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fileSize INTEGER,
            author TEXT,
            year TEXT,
            language TEXT,
            fileType TEXT,
            collection TEXT,
            fileMtime REAL,
            totalTokens INTEGER
        )
    """)

    # Chunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages_chunks (
            id TEXT PRIMARY KEY,
            docId TEXT,
            pageNum INTEGER,
            chunkId TEXT,
            content TEXT,
            sectionHeader TEXT,
            startChar INTEGER,
            endChar INTEGER,
            tokenCount INTEGER,
            prevId TEXT,
            nextId TEXT,
            FOREIGN KEY(docId) REFERENCES documents(id)
        )
    """)

    # FTS5 virtual table for fast full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            content,
            docId UNINDEXED,
            chunkId UNINDEXED,
            content='pages_chunks',
            content_rowid='rowid'
        )
    """)

    # Triggers to keep FTS table in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON pages_chunks BEGIN
            INSERT INTO chunks_fts(rowid, content, docId, chunkId)
            VALUES (new.rowid, new.content, new.docId, new.chunkId);
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON pages_chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content, docId, chunkId)
            VALUES ('delete', old.rowid, old.content, old.docId, old.chunkId);
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON pages_chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content, docId, chunkId)
            VALUES ('delete', old.rowid, old.content, old.docId, old.chunkId);
            INSERT INTO chunks_fts(rowid, content, docId, chunkId)
            VALUES (new.rowid, new.content, new.docId, new.chunkId);
        END;
    """)

    # BM25 Statistics Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS term_df (
            term TEXT PRIMARY KEY,
            doc_freq INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS term_freq (
            docId TEXT,
            term TEXT,
            freq INTEGER,
            PRIMARY KEY (docId, term),
            FOREIGN KEY(docId) REFERENCES documents(id)
        )
    """)

    conn.commit()
    conn.close()
