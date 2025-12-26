def regex_match(text: str, pattern: str) -> bool:
    """
    Implements simple regex matching with support for:
    - '.' matches any single character
    - '*' matches zero or more of the preceding element

    Args:
        text: The input string to match
        pattern: The regex pattern (supports '.' and '*')

    Returns:
        True if the entire text matches the pattern, False otherwise
    """
    m, n = len(text), len(pattern)

    # dp[i][j] = True if text[0:i] matches pattern[0:j]
    dp = [[False] * (n + 1) for _ in range(m + 1)]

    # Empty pattern matches empty text
    dp[0][0] = True

    # Handle patterns like a*, a*b*, a*b*c* that can match empty text
    for j in range(2, n + 1):
        if pattern[j - 1] == '*':
            dp[0][j] = dp[0][j - 2]

    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pattern[j - 1] == '*':
                # '*' can mean zero occurrences of the preceding element
                dp[i][j] = dp[i][j - 2]

                # Or one or more occurrences if the preceding element matches
                if pattern[j - 2] == '.' or pattern[j - 2] == text[i - 1]:
                    dp[i][j] = dp[i][j] or dp[i - 1][j]

            elif pattern[j - 1] == '.' or pattern[j - 1] == text[i - 1]:
                # Current characters match (or pattern has '.')
                dp[i][j] = dp[i - 1][j - 1]

    return dp[m][n]


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("aa", "a", False),
        ("aa", "a*", True),
        ("ab", ".*", True),
        ("aab", "c*a*b", True),
        ("mississippi", "mis*is*p*.", False),
        ("", "", True),
        ("", "a*", True),
        ("abc", "abc", True),
        ("abc", "a.c", True),
        ("abc", "a.*c", True),
        ("aaa", "a*a", True),
        ("ab", ".*c", False),
    ]

    print("Testing regex_match function:")
    print("-" * 50)

    all_passed = True
    for text, pattern, expected in test_cases:
        result = regex_match(text, pattern)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"{status}: regex_match('{text}', '{pattern}') = {result} (expected {expected})")

    print("-" * 50)
    print(f"All tests passed: {all_passed}")
