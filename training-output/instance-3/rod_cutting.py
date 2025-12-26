def rod_cutting(prices: list[int], n: int) -> tuple[int, list[int]]:
    """
    Solve the rod cutting problem using dynamic programming.

    Given a rod of length n and a list of prices for each length,
    find the maximum profit obtainable by cutting the rod into pieces.

    Args:
        prices: List where prices[i] is the price of a rod of length i+1.
        n: Length of the rod to cut.

    Returns:
        A tuple of (max_profit, cuts) where cuts is the list of piece lengths.
    """
    if n == 0:
        return 0, []

    # dp[i] stores the maximum profit for rod of length i
    dp = [0] * (n + 1)
    # parent[i] stores the first cut that gives optimal solution for length i
    parent = [0] * (n + 1)

    for i in range(1, n + 1):
        max_val = float('-inf')
        for j in range(1, i + 1):
            if j <= len(prices) and dp[i - j] + prices[j - 1] > max_val:
                max_val = dp[i - j] + prices[j - 1]
                parent[i] = j
        dp[i] = max_val

    # Reconstruct the cuts
    cuts = []
    remaining = n
    while remaining > 0:
        cuts.append(parent[remaining])
        remaining -= parent[remaining]

    return dp[n], cuts


if __name__ == "__main__":
    # Example usage
    prices = [1, 5, 8, 9, 10, 17, 17, 20]
    rod_length = 8

    max_profit, cuts = rod_cutting(prices, rod_length)
    print(f"Rod length: {rod_length}")
    print(f"Prices: {prices}")
    print(f"Maximum profit: {max_profit}")
    print(f"Optimal cuts: {cuts}")
