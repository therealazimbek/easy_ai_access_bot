import nltk
from nltk.tokenize import word_tokenize

nltk.download("punkt")


def validate_user_input(user_input, max_tokens=4096) -> bool:
    tokens = word_tokenize(user_input)
    token_count = len(tokens)

    if token_count > max_tokens or token_count <= 0:
        return False

    return True
