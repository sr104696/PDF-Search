import math
from src.index.schema import get_db_connection

def calculate_bm25_scores(query_terms: list[str], candidate_doc_ids: list[str]) -> dict[str, float]:
    """
    Calculates BM25 scores for a set of candidate documents based on query terms.
    k1 and b are standard BM25 parameters.
    """
    if not query_terms or not candidate_doc_ids:
        return {}

    k1 = 1.5
    b = 0.75

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get total number of documents (N)
    cursor.execute("SELECT COUNT(*) as count FROM documents")
    N = cursor.fetchone()['count']
    if N == 0:
        conn.close()
        return {}

    # Get average document length (avgdl) in tokens
    cursor.execute("SELECT AVG(totalTokens) as avgdl FROM documents")
    avgdl = cursor.fetchone()['avgdl']
    if not avgdl or avgdl == 0:
        avgdl = 1.0

    scores = {doc_id: 0.0 for doc_id in candidate_doc_ids}

    for term in query_terms:
        # Get document frequency (df) for the term
        cursor.execute("SELECT doc_freq FROM term_df WHERE term = ?", (term,))
        row = cursor.fetchone()
        df = row['doc_freq'] if row else 0

        # Calculate Inverse Document Frequency (IDF)
        # Using a standard BM25 IDF formulation with floor
        idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
        if idf < 0:
            idf = 0.01 # Floor to avoid negative scores for stop words if not properly filtered

        if df == 0:
            continue # Term not in corpus

        # Get term frequencies for all candidate docs
        placeholders = ','.join(['?'] * len(candidate_doc_ids))
        cursor.execute(f"""
            SELECT d.id as docId, d.totalTokens, tf.freq
            FROM documents d
            LEFT JOIN term_freq tf ON d.id = tf.docId AND tf.term = ?
            WHERE d.id IN ({placeholders})
        """, [term] + candidate_doc_ids)

        for row in cursor.fetchall():
            doc_id = row['docId']
            tf = row['freq'] if row['freq'] else 0
            doc_len = row['totalTokens'] if row['totalTokens'] else 0

            if tf > 0:
                # BM25 Term Frequency weighting
                tf_weight = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                scores[doc_id] += idf * tf_weight

    conn.close()
    return scores
