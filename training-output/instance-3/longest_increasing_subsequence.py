def longest_increasing_subsequence(nums: list[int]) -> list[int]:
    """
    Find the longest increasing subsequence using dynamic programming.

    Args:
        nums: A list of integers

    Returns:
        The longest increasing subsequence as a list
    """
    if not nums:
        return []

    n = len(nums)

    # dp[i] stores the length of LIS ending at index i
    dp = [1] * n

    # parent[i] stores the index of the previous element in the LIS ending at i
    parent = [-1] * n

    # Fill dp table
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                parent[i] = j

    # Find the index with maximum LIS length
    max_length = max(dp)
    max_index = dp.index(max_length)

    # Reconstruct the subsequence
    result = []
    current = max_index
    while current != -1:
        result.append(nums[current])
        current = parent[current]

    return result[::-1]


if __name__ == "__main__":
    # Test cases
    test1 = [10, 9, 2, 5, 3, 7, 101, 18]
    print(f"Input: {test1}")
    print(f"LIS: {longest_increasing_subsequence(test1)}")

    test2 = [0, 1, 0, 3, 2, 3]
    print(f"\nInput: {test2}")
    print(f"LIS: {longest_increasing_subsequence(test2)}")

    test3 = [7, 7, 7, 7, 7]
    print(f"\nInput: {test3}")
    print(f"LIS: {longest_increasing_subsequence(test3)}")

    test4 = []
    print(f"\nInput: {test4}")
    print(f"LIS: {longest_increasing_subsequence(test4)}")
