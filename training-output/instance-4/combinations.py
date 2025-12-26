def combinations(iterable, r):
    """
    Generate all r-combinations from the given iterable.

    Args:
        iterable: An iterable to generate combinations from
        r: The length of each combination

    Yields:
        Tuples of length r containing combinations of elements
    """
    pool = tuple(iterable)
    n = len(pool)

    if r > n or r < 0:
        return

    indices = list(range(r))
    yield tuple(pool[i] for i in indices)

    while True:
        # Find the rightmost index that can be incremented
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return

        # Increment this index and reset all indices to its right
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1

        yield tuple(pool[i] for i in indices)
