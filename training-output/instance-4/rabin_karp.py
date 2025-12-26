def rabin_karp(text: str, pattern: str) -> list[int]:
    """
    Rabin-Karp pattern matching algorithm.

    Args:
        text: The text to search in
        pattern: The pattern to search for

    Returns:
        List of starting indices where pattern is found in text
    """
    if not pattern or not text or len(pattern) > len(text):
        return []

    base = 256  # Number of characters in the alphabet
    mod = 101   # A prime number for modular arithmetic

    n = len(text)
    m = len(pattern)
    results = []

    # Calculate hash value for pattern and first window of text
    pattern_hash = 0
    text_hash = 0
    h = pow(base, m - 1, mod)  # base^(m-1) % mod

    for i in range(m):
        pattern_hash = (base * pattern_hash + ord(pattern[i])) % mod
        text_hash = (base * text_hash + ord(text[i])) % mod

    # Slide the pattern over text
    for i in range(n - m + 1):
        # Check if hash values match
        if pattern_hash == text_hash:
            # Verify character by character to handle hash collisions
            if text[i:i + m] == pattern:
                results.append(i)

        # Calculate hash for next window (rolling hash)
        if i < n - m:
            text_hash = (base * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % mod
            # Handle negative hash values
            if text_hash < 0:
                text_hash += mod

    return results
