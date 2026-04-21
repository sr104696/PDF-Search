import re

def tokenize(text: str) -> list[str]:
    """Basic tokenizer that splits by words/punctuation and returns lowercased tokens."""
    return [word.lower() for word in re.findall(r'\b\w+\b', text)]

def count_tokens(text: str) -> int:
    return len(tokenize(text))
