class SegmentTree:
    """Segment Tree for range sum queries with point updates.

    Time Complexity:
        - Build: O(n)
        - Update: O(log n)
        - Query: O(log n)

    Space Complexity: O(n)
    """

    def __init__(self, arr: list[int | float]):
        """Initialize the segment tree with the given array.

        Args:
            arr: Input array of numbers.
        """
        self.n = len(arr)
        if self.n == 0:
            self.tree = []
            return

        self.tree = [0] * (2 * self.n)

        # Build the tree - leaves are in tree[n:2n]
        for i in range(self.n):
            self.tree[self.n + i] = arr[i]

        # Build internal nodes
        for i in range(self.n - 1, 0, -1):
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]

    def update(self, index: int, value: int | float) -> None:
        """Update the value at the given index.

        Args:
            index: Index to update (0-based).
            value: New value to set.

        Raises:
            IndexError: If index is out of bounds.
        """
        if index < 0 or index >= self.n:
            raise IndexError(f"Index {index} out of range [0, {self.n})")

        pos = index + self.n
        self.tree[pos] = value

        # Update ancestors
        while pos > 1:
            pos //= 2
            self.tree[pos] = self.tree[2 * pos] + self.tree[2 * pos + 1]

    def query(self, left: int, right: int) -> int | float:
        """Return the sum of elements in range [left, right] (inclusive).

        Args:
            left: Left bound (0-based, inclusive).
            right: Right bound (0-based, inclusive).

        Returns:
            Sum of elements in the range.

        Raises:
            ValueError: If range is invalid.
        """
        if self.n == 0:
            raise ValueError("Cannot query empty segment tree")
        if left < 0 or right >= self.n or left > right:
            raise ValueError(f"Invalid range [{left}, {right}] for array of size {self.n}")

        result = 0
        left += self.n
        right += self.n + 1

        while left < right:
            if left & 1:
                result += self.tree[left]
                left += 1
            if right & 1:
                right -= 1
                result += self.tree[right]
            left //= 2
            right //= 2

        return result


if __name__ == "__main__":
    # Example usage
    arr = [1, 3, 5, 7, 9, 11]
    st = SegmentTree(arr)

    print(f"Array: {arr}")
    print(f"Sum of range [1, 3]: {st.query(1, 3)}")  # 3 + 5 + 7 = 15

    st.update(2, 10)  # Change index 2 from 5 to 10
    print(f"After updating index 2 to 10:")
    print(f"Sum of range [1, 3]: {st.query(1, 3)}")  # 3 + 10 + 7 = 20
