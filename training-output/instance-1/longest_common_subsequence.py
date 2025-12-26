def longest_common_subsequence(s1: str, s2: str) -> str:
    """
    Find the longest common subsequence of two strings using dynamic programming.

    Args:
        s1: First string
        s2: Second string

    Returns:
        The longest common subsequence string
    """
    m, n = len(s1), len(s2)

    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Backtrack to find the LCS string
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    return ''.join(reversed(lcs))


if __name__ == "__main__":
    # Test examples
    print(longest_common_subsequence("ABCDGH", "AEDFHR"))  # "ADH"
    print(longest_common_subsequence("AGGTAB", "GXTXAYB"))  # "GTAB"
    print(longest_common_subsequence("abc", "abc"))  # "abc"
    print(longest_common_subsequence("abc", "def"))  # ""
