def knapsack_01(weights: list[int], values: list[int], capacity: int) -> int:
    """
    Solve the 0/1 knapsack problem using dynamic programming.

    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum weight capacity of the knapsack

    Returns:
        Maximum value that can be achieved within the capacity
    """
    n = len(weights)

    # dp[w] represents the maximum value achievable with capacity w
    dp = [0] * (capacity + 1)

    for i in range(n):
        # Traverse backwards to avoid using the same item twice
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])

    return dp[capacity]


# Alias for consistency with instance-1
knapsack = knapsack_01
