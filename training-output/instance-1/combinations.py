def combinations(lst, r):
    """
    Generate all r-combinations of a list.

    Args:
        lst: Input list of elements
        r: Size of each combination

    Yields:
        Tuples containing r elements from the list
    """
    n = len(lst)
    if r > n or r < 0:
        return
    if r == 0:
        yield ()
        return

    indices = list(range(r))
    yield tuple(lst[i] for i in indices)

    while True:
        # Find the rightmost index that can be incremented
        for i in range(r - 1, -1, -1):
            if indices[i] != i + n - r:
                break
        else:
            return

        # Increment this index and reset all following indices
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1

        yield tuple(lst[i] for i in indices)


if __name__ == "__main__":
    # Example usage
    items = [1, 2, 3, 4]
    print(f"All 2-combinations of {items}:")
    for combo in combinations(items, 2):
        print(combo)

    print(f"\nAll 3-combinations of {items}:")
    for combo in combinations(items, 3):
        print(combo)
