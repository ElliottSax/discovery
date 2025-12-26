def permutations(lst):
    """Generate all permutations of a list."""
    if len(lst) <= 1:
        yield lst[:]
        return

    for i in range(len(lst)):
        rest = lst[:i] + lst[i+1:]
        for perm in permutations(rest):
            yield [lst[i]] + perm


if __name__ == "__main__":
    # Example usage
    result = list(permutations([1, 2, 3]))
    print(f"Permutations of [1, 2, 3]: {result}")
