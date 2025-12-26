class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def tree_depth(root: TreeNode | None) -> int:
    """
    Calculate the maximum depth of a binary tree.

    The maximum depth is the number of nodes along the longest path
    from the root node down to the farthest leaf node.

    Args:
        root: The root node of the binary tree, or None for an empty tree.

    Returns:
        The maximum depth of the tree. Returns 0 for an empty tree.
    """
    if root is None:
        return 0

    left_depth = tree_depth(root.left)
    right_depth = tree_depth(root.right)

    return max(left_depth, right_depth) + 1
