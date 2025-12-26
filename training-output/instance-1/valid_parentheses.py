def valid_parentheses(s: str) -> bool:
    """
    Check if a string has valid bracket matching.

    Supports: (), [], {}

    Args:
        s: Input string containing brackets

    Returns:
        True if all brackets are properly matched and nested, False otherwise
    """
    stack = []
    bracket_map = {')': '(', ']': '[', '}': '{'}

    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in ')]}':
            if not stack or stack[-1] != bracket_map[char]:
                return False
            stack.pop()

    return len(stack) == 0
