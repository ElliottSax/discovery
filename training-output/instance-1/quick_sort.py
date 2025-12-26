def quick_sort(arr):
    """
    Sorts an array using the quicksort algorithm.

    Args:
        arr: List of comparable elements to sort

    Returns:
        A new sorted list
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quick_sort(left) + middle + quick_sort(right)
