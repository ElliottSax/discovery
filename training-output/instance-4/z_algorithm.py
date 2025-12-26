def z_algorithm(text: str, pattern: str) -> list[int]:
    """
    Z-algorithm for pattern matching.

    The Z-algorithm finds all occurrences of a pattern in a text in O(n + m) time.
    It works by computing the Z-array, where Z[i] is the length of the longest
    substring starting at position i that matches a prefix of the string.

    Args:
        text: The text to search in
        pattern: The pattern to search for

    Returns:
        List of starting indices where pattern is found in text
    """
    if not pattern or not text or len(pattern) > len(text):
        return []

    # Concatenate pattern + separator + text
    # The separator must not appear in pattern or text
    concat = pattern + "$" + text
    n = len(concat)
    m = len(pattern)

    # Build Z-array
    z = [0] * n
    z[0] = n  # Z[0] is defined as the length of the string

    left, right = 0, 0  # Z-box boundaries

    for i in range(1, n):
        if i > right:
            # Case 1: i is outside the Z-box, compute Z[i] naively
            left, right = i, i
            while right < n and concat[right - left] == concat[right]:
                right += 1
            z[i] = right - left
            right -= 1
        else:
            # Case 2: i is inside the Z-box
            k = i - left  # Corresponding position in the prefix

            if z[k] < right - i + 1:
                # Case 2a: Z[k] is less than remaining Z-box length
                z[i] = z[k]
            else:
                # Case 2b: Z[k] reaches or exceeds the Z-box boundary
                left = i
                while right < n and concat[right - left] == concat[right]:
                    right += 1
                z[i] = right - left
                right -= 1

    # Find all positions where Z[i] equals the pattern length
    results = []
    for i in range(m + 1, n):  # Skip pattern and separator
        if z[i] == m:
            results.append(i - m - 1)  # Convert to position in original text

    return results
