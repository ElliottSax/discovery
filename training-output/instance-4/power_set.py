def power_set(s):
    """
    Generate all subsets (power set) of the given iterable.

    Args:
        s: An iterable (list, set, tuple, etc.)

    Returns:
        A list of lists containing all possible subsets.
    """
    items = list(s)
    n = len(items)
    result = []

    # There are 2^n subsets for a set of n elements
    for i in range(2 ** n):
        subset = []
        for j in range(n):
            # Check if j-th bit is set in i
            if i & (1 << j):
                subset.append(items[j])
        result.append(subset)

    return result


if __name__ == "__main__":
    # Example usage
    print(power_set([1, 2, 3]))
    # Output: [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]
