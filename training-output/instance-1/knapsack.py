def knapsack(weights: list[int], values: list[int], capacity: int) -> int:
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

    # dp[i][w] = max value using first i items with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i - 1][w]

            # Take item i-1 if it fits
            if weights[i - 1] <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - weights[i - 1]] + values[i - 1])

    return dp[n][capacity]
