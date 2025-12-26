def longest_palindrome(s: str) -> str:
    """
    Find the longest palindromic substring in a string.

    Uses the expand-around-center approach for O(n²) time complexity
    and O(1) space complexity.

    Args:
        s: Input string

    Returns:
        The longest palindromic substring
    """
    if not s:
        return ""

    def expand_around_center(left: int, right: int) -> str:
        """Expand outward from center while characters match."""
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return s[left + 1:right]

    longest = ""

    for i in range(len(s)):
        # Odd-length palindromes (single center)
        odd = expand_around_center(i, i)
        if len(odd) > len(longest):
            longest = odd

        # Even-length palindromes (two-character center)
        even = expand_around_center(i, i + 1)
        if len(even) > len(longest):
            longest = even

    return longest
