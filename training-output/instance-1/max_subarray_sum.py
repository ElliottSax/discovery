def max_subarray_sum(arr):
    """
    Find the maximum sum contiguous subarray using Kadane's algorithm.

    Args:
        arr: List of numbers (can be positive, negative, or zero)

    Returns:
        The maximum sum of any contiguous subarray
    """
    if not arr:
        return 0

    max_ending_here = arr[0]
    max_so_far = arr[0]

    for num in arr[1:]:
        max_ending_here = max(num, max_ending_here + num)
        max_so_far = max(max_so_far, max_ending_here)

    return max_so_far
