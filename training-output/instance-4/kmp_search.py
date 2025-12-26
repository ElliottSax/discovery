def kmp_search(text: str, pattern: str) -> list[int]:
    """
    Implements the Knuth-Morris-Pratt string matching algorithm.

    Args:
        text: The text to search in.
        pattern: The pattern to search for.

    Returns:
        A list of starting indices where the pattern is found in the text.
    """
    if not pattern:
        return []

    # Build the failure function (partial match table)
    lps = _build_lps(pattern)

    matches = []
    j = 0  # Index for pattern

    for i in range(len(text)):
        # Mismatch: use LPS to skip comparisons
        while j > 0 and text[i] != pattern[j]:
            j = lps[j - 1]

        # Match: advance pattern index
        if text[i] == pattern[j]:
            j += 1

        # Full pattern matched
        if j == len(pattern):
            matches.append(i - j + 1)
            j = lps[j - 1]

    return matches


def _build_lps(pattern: str) -> list[int]:
    """
    Builds the Longest Proper Prefix which is also Suffix (LPS) array.

    Args:
        pattern: The pattern to build the LPS array for.

    Returns:
        The LPS array where lps[i] is the length of the longest proper
        prefix of pattern[0:i+1] which is also a suffix.
    """
    lps = [0] * len(pattern)
    length = 0  # Length of previous longest prefix suffix
    i = 1

    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length > 0:
            # Use previously computed LPS value
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1

    return lps


if __name__ == "__main__":
    # Example usage
    text = "ABABDABACDABABCABAB"
    pattern = "ABABCABAB"

    result = kmp_search(text, pattern)
    print(f"Pattern '{pattern}' found at indices: {result}")

    # More examples
    print(kmp_search("AAAAAAA", "AAA"))  # [0, 1, 2, 3, 4]
    print(kmp_search("ABCDEF", "XYZ"))   # []
    print(kmp_search("ABABABAB", "ABAB"))  # [0, 2, 4]
