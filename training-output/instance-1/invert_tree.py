class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def invert_tree(root: TreeNode | None) -> TreeNode | None:
    """
    Invert a binary tree by swapping left and right children at every node.

    Args:
        root: The root node of the binary tree, or None for an empty tree.

    Returns:
        The root of the inverted tree, or None if the input was empty.
    """
    if root is None:
        return None

    root.left, root.right = root.right, root.left

    invert_tree(root.left)
    invert_tree(root.right)

    return root
