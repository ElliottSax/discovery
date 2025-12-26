def merge_sorted_lists(list1: list, list2: list) -> list:
    """
    Merge two sorted lists into one sorted list efficiently.

    Uses a two-pointer approach for O(n + m) time complexity.

    Args:
        list1: First sorted list
        list2: Second sorted list

    Returns:
        A new sorted list containing all elements from both lists
    """
    result = []
    i = j = 0

    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1

    # Append remaining elements
    result.extend(list1[i:])
    result.extend(list2[j:])

    return result
