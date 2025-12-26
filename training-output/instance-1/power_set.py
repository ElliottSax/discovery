def power_set(s):
    """
    Generate all subsets (power set) of a given set.

    Args:
        s: An iterable (set, list, tuple, etc.)

    Returns:
        A list of lists containing all subsets
    """
    elements = list(s)
    n = len(elements)
    result = []

    # Iterate through all 2^n possible combinations
    for i in range(2 ** n):
        subset = []
        for j in range(n):
            # Check if j-th bit is set in i
            if i & (1 << j):
                subset.append(elements[j])
        result.append(subset)

    return result


if __name__ == "__main__":
    # Example usage
    test_set = {1, 2, 3}
    print(f"Power set of {test_set}:")
    for subset in power_set(test_set):
        print(f"  {subset}")
