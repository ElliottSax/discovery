def longest_palindrome_substring(s: str) -> str:
    """
    Find the longest palindromic substring in a given string.

    Uses the expand-around-center approach for O(n²) time complexity
    and O(1) space complexity.

    Args:
        s: Input string to search for palindromic substrings.

    Returns:
        The longest palindromic substring found.
    """
    if not s or len(s) < 1:
        return ""

    start = 0
    end = 0

    def expand_around_center(left: int, right: int) -> int:
        """Expand around center and return the length of the palindrome."""
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return right - left - 1

    for i in range(len(s)):
        # Odd length palindromes (single character center)
        len1 = expand_around_center(i, i)
        # Even length palindromes (two character center)
        len2 = expand_around_center(i, i + 1)

        max_len = max(len1, len2)

        if max_len > end - start:
            start = i - (max_len - 1) // 2
            end = i + max_len // 2

    return s[start:end + 1]


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "babad",
        "cbbd",
        "a",
        "ac",
        "racecar",
        "bananas",
        "",
    ]

    for test in test_cases:
        result = longest_palindrome_substring(test)
        print(f"Input: '{test}' -> Longest palindrome: '{result}'")
