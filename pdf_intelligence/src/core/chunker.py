import re
from src.core.tokenizer import count_tokens

def chunk_text(text: str, max_tokens: int = 512) -> list[dict]:
    """
    Chunks text into smaller pieces.
    Attempts to split by paragraphs, then sentences if necessary.
    Returns a list of dicts: [{'text': '...', 'start_char': 0, 'end_char': 100, 'token_count': 20}, ...]
    """
    chunks = []

    # Split by double newline (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)

    current_chunk = ""
    current_start = 0
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        # If paragraph is too big, split by sentences (fallback simple regex)
        if para_tokens > max_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                sent_tokens = count_tokens(sent)
                if current_tokens + sent_tokens > max_tokens and current_chunk:
                    end_char = current_start + len(current_chunk)
                    chunks.append({
                        "text": current_chunk.strip(),
                        "start_char": current_start,
                        "end_char": end_char,
                        "token_count": current_tokens
                    })
                    current_chunk = sent + " "
                    current_start = end_char
                    current_tokens = sent_tokens
                else:
                    current_chunk += sent + " "
                    current_tokens += sent_tokens
        else:
            if current_tokens + para_tokens > max_tokens and current_chunk:
                end_char = current_start + len(current_chunk)
                chunks.append({
                    "text": current_chunk.strip(),
                    "start_char": current_start,
                    "end_char": end_char,
                    "token_count": current_tokens
                })
                current_chunk = para + "\n\n"
                current_start = end_char
                current_tokens = para_tokens
            else:
                current_chunk += para + "\n\n"
                current_tokens += para_tokens

    if current_chunk.strip():
        end_char = current_start + len(current_chunk)
        chunks.append({
            "text": current_chunk.strip(),
            "start_char": current_start,
            "end_char": end_char,
            "token_count": current_tokens
        })

    return chunks
