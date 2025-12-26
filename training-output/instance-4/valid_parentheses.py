def valid_parentheses(s: str) -> bool:
    """
    Check if a string has balanced brackets.

    Supports (), [], and {} bracket pairs.

    Args:
        s: Input string containing brackets to validate

    Returns:
        True if all brackets are properly balanced, False otherwise
    """
    stack = []
    bracket_pairs = {')': '(', ']': '[', '}': '{'}

    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in ')]}':
            if not stack or stack[-1] != bracket_pairs[char]:
                return False
            stack.pop()

    return len(stack) == 0
