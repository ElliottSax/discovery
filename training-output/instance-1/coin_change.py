def coin_change(coins: list[int], amount: int) -> int:
    """
    Find the minimum number of coins needed to make up the given amount.

    Args:
        coins: List of coin denominations available
        amount: Target amount to make

    Returns:
        Minimum number of coins needed, or -1 if the amount cannot be made
    """
    # dp[i] = minimum coins needed to make amount i
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # 0 coins needed to make amount 0

    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i and dp[i - coin] != float('inf'):
                dp[i] = min(dp[i], dp[i - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1
