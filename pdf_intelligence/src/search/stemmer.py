try:
    import snowballstemmer
    _stemmer = snowballstemmer.stemmer('english')
except ImportError:
    _stemmer = None

def stem_word(word: str) -> str:
    """Stem a single word using Snowball stemmer, fallback to original if unavailable."""
    if _stemmer:
        return _stemmer.stemWord(word)
    return word

def stem_text(text: str) -> list[str]:
    """Stem a list of words."""
    from src.core.tokenizer import tokenize
    words = tokenize(text)
    return [stem_word(w) for w in words]
