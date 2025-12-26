def next_permutation(nums: list) -> bool:
    """
    Find the lexicographically next permutation of a list in-place.

    Args:
        nums: A list of elements to permute (modified in-place)

    Returns:
        True if a next permutation exists, False if already at the last permutation
        (in which case the list is reset to the first permutation)
    """
    n = len(nums)
    if n <= 1:
        return False

    # Step 1: Find the largest index i such that nums[i] < nums[i + 1]
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1

    if i < 0:
        # Already at the last permutation, reverse to get the first
        nums.reverse()
        return False

    # Step 2: Find the largest index j such that nums[i] < nums[j]
    j = n - 1
    while nums[j] <= nums[i]:
        j -= 1

    # Step 3: Swap nums[i] and nums[j]
    nums[i], nums[j] = nums[j], nums[i]

    # Step 4: Reverse the suffix starting at i + 1
    left, right = i + 1, n - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1

    return True


if __name__ == "__main__":
    # Example usage
    test = [1, 2, 3]
    print(f"Starting: {test}")
    while next_permutation(test):
        print(f"Next:     {test}")
    print(f"Wrapped:  {test}")
