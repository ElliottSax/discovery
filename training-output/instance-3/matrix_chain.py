def matrix_chain(dimensions: list[int]) -> tuple[int, str]:
    """
    Find the optimal order for multiplying a chain of matrices.

    Uses dynamic programming to minimize the total number of scalar multiplications.

    Args:
        dimensions: List of matrix dimensions where matrix i has dimensions
                   dimensions[i] x dimensions[i+1]. For n matrices, this list
                   has n+1 elements.

    Returns:
        A tuple containing:
        - The minimum number of scalar multiplications needed
        - A string showing the optimal parenthesization

    Example:
        >>> matrix_chain([10, 30, 5, 60])
        (4500, '((A1 x A2) x A3)')
        # Matrix A1: 10x30, A2: 30x5, A3: 5x60
        # Optimal: (A1 x A2) first, then multiply by A3
    """
    n = len(dimensions) - 1  # Number of matrices

    if n <= 0:
        return (0, "")

    if n == 1:
        return (0, "A1")

    # dp[i][j] = minimum cost to multiply matrices i through j
    dp = [[0] * n for _ in range(n)]

    # split[i][j] = optimal split point for matrices i through j
    split = [[0] * n for _ in range(n)]

    # Fill the table for chains of increasing length
    for chain_len in range(2, n + 1):
        for i in range(n - chain_len + 1):
            j = i + chain_len - 1
            dp[i][j] = float('inf')

            # Try all possible split points
            for k in range(i, j):
                # Cost = cost of left subchain + cost of right subchain +
                #        cost of multiplying the two resulting matrices
                cost = (dp[i][k] + dp[k + 1][j] +
                       dimensions[i] * dimensions[k + 1] * dimensions[j + 1])

                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k

    def build_parenthesization(i: int, j: int) -> str:
        """Recursively build the optimal parenthesization string."""
        if i == j:
            return f"A{i + 1}"

        k = split[i][j]
        left = build_parenthesization(i, k)
        right = build_parenthesization(k + 1, j)

        return f"({left} x {right})"

    optimal_order = build_parenthesization(0, n - 1)

    return (dp[0][n - 1], optimal_order)


if __name__ == "__main__":
    # Example usage
    dims = [10, 30, 5, 60]
    min_cost, order = matrix_chain(dims)
    print(f"Dimensions: {dims}")
    print(f"Minimum multiplications: {min_cost}")
    print(f"Optimal order: {order}")

    print()

    # Another example with more matrices
    dims2 = [40, 20, 30, 10, 30]
    min_cost2, order2 = matrix_chain(dims2)
    print(f"Dimensions: {dims2}")
    print(f"Minimum multiplications: {min_cost2}")
    print(f"Optimal order: {order2}")
