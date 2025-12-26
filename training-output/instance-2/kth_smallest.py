class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def kth_smallest(root: TreeNode, k: int) -> int:
    """
    Find the kth smallest element in a Binary Search Tree.

    Uses in-order traversal (left -> root -> right) which visits
    BST nodes in ascending order.

    Args:
        root: Root node of the BST
        k: The kth position (1-indexed)

    Returns:
        The kth smallest value in the BST
    """
    stack = []
    current = root
    count = 0

    while stack or current:
        # Go to the leftmost node
        while current:
            stack.append(current)
            current = current.left

        # Process current node
        current = stack.pop()
        count += 1

        if count == k:
            return current.val

        # Move to right subtree
        current = current.right

    return -1  # k is larger than number of nodes
