class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def is_balanced_tree(root: TreeNode | None) -> bool:
    """
    Check if a binary tree is height-balanced.

    A height-balanced binary tree is defined as a binary tree in which
    the depth of the two subtrees of every node never differs by more than 1.

    Args:
        root: The root node of the binary tree.

    Returns:
        True if the tree is height-balanced, False otherwise.
    """
    def check_height(node: TreeNode | None) -> int:
        """
        Returns the height of the subtree if balanced, -1 if unbalanced.
        """
        if node is None:
            return 0

        left_height = check_height(node.left)
        if left_height == -1:
            return -1

        right_height = check_height(node.right)
        if right_height == -1:
            return -1

        if abs(left_height - right_height) > 1:
            return -1

        return max(left_height, right_height) + 1

    return check_height(root) != -1
