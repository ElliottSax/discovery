class MinHeap:
    """A min-heap implementation where the smallest element is at the root."""

    def __init__(self):
        self.heap = []

    def _parent(self, index):
        return (index - 1) // 2

    def _left_child(self, index):
        return 2 * index + 1

    def _right_child(self, index):
        return 2 * index + 2

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def _sift_up(self, index):
        """Move element up to maintain heap property."""
        while index > 0 and self.heap[self._parent(index)] > self.heap[index]:
            self._swap(index, self._parent(index))
            index = self._parent(index)

    def _sift_down(self, index):
        """Move element down to maintain heap property."""
        size = len(self.heap)
        smallest = index

        left = self._left_child(index)
        if left < size and self.heap[left] < self.heap[smallest]:
            smallest = left

        right = self._right_child(index)
        if right < size and self.heap[right] < self.heap[smallest]:
            smallest = right

        if smallest != index:
            self._swap(index, smallest)
            self._sift_down(smallest)

    def insert(self, value):
        """Insert a value into the heap."""
        self.heap.append(value)
        self._sift_up(len(self.heap) - 1)

    def extract_min(self):
        """Remove and return the minimum element."""
        if not self.heap:
            raise IndexError("extract_min from empty heap")

        min_val = self.heap[0]
        last = self.heap.pop()

        if self.heap:
            self.heap[0] = last
            self._sift_down(0)

        return min_val

    def heapify(self, array):
        """Build a heap from an array in O(n) time."""
        self.heap = array[:]
        for i in range(len(self.heap) // 2 - 1, -1, -1):
            self._sift_down(i)

    def peek(self):
        """Return the minimum element without removing it."""
        if not self.heap:
            raise IndexError("peek from empty heap")
        return self.heap[0]

    def __len__(self):
        return len(self.heap)

    def __bool__(self):
        return bool(self.heap)

    def __repr__(self):
        return f"MinHeap({self.heap})"
