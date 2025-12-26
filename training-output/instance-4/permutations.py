def permutations(items):
    """
    Generate all permutations of the given items.

    Args:
        items: An iterable of items to permute.

    Yields:
        Tuples containing each permutation.
    """
    items = list(items)
    n = len(items)

    if n == 0:
        yield ()
        return

    if n == 1:
        yield (items[0],)
        return

    for i in range(n):
        current = items[i]
        remaining = items[:i] + items[i+1:]
        for perm in permutations(remaining):
            yield (current,) + perm
