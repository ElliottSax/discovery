def word_break(s: str, word_dict: list[str]) -> bool:
    """
    Determine if a string can be segmented into space-separated dictionary words.

    Args:
        s: The input string to segment
        word_dict: List of valid dictionary words

    Returns:
        True if s can be segmented into dictionary words, False otherwise
    """
    if not s:
        return True

    word_set = set(word_dict)
    n = len(s)

    # dp[i] = True means s[0:i] can be segmented into dictionary words
    dp = [False] * (n + 1)
    dp[0] = True  # Empty string can always be segmented

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break

    return dp[n]


if __name__ == "__main__":
    # Test cases
    print(word_break("leetcode", ["leet", "code"]))  # True
    print(word_break("applepenapple", ["apple", "pen"]))  # True
    print(word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]))  # False
    print(word_break("", ["a", "b"]))  # True (empty string)
    print(word_break("a", []))  # False (empty dictionary)
